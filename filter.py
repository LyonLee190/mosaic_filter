import argparse
import cv2
import os
import re

class imgProcess:
    def __init__(self, targetDir, sampleDir, fileType, height, width):
        '''
        targetDir:      path to the target image
        sampleDir:      path to the directory containing sample images
        height & with:  size of the sample image,
                        also used as the size of the tile in the mosaic painting
        '''
        self.targetDir = targetDir
        self.sampleDir = sampleDir
        self.fileType = fileType
        self.height = height
        self.width= width

    def load_samples(self):
        '''
        Loads sample images and resizes them.
        '''
        sampleSet = []
        for filename in os.listdir(self.sampleDir):
            # validate the file type
            if not re.search(self.fileType, filename, re.I):
                continue
            filepath = os.path.join(self.sampleDir, filename)

            # open and resize the sample
            img = cv2.imread(filepath)
            resized = cv2.resize(img, (self.width, self.height), interpolation=cv2.INTER_AREA)
            sampleSet.append(resized)

        return sampleSet

    def mosaic(self, outputDir, bins, option):
        '''
        Splits the target image into tiles.
        Replaces each tile with the sample whose RGB histogram is closet to it in the image set.
        Generates the filtered image.

        outputDir:  path to the directory containing the output image
        bins:       # of bins per channel when calculating histogram
        option:     for calculating the difference between two histograms
                    -- correlation
                    -- chi-squared
                    -- intersection
                    -- hellinger
        '''
        img = cv2.imread(self.targetDir)
        H, W = img.shape[:2]
        if H < self.height or W < self.width:
            print("Failed to crop " + self.targetDir + ": out of the boundary.")
            exit(0)
        H = H - H % self.height
        W = W - W % self.width

        croppedImg = img[0:H, 0:W].copy()
        sampleSet = self.load_samples()

        for row in range(0, H, self.height):
            for col in range(0, W, self.width):
                # split the target image into tiles
                tile = croppedImg[row:row + self.height, col:col + self.width]
                # for each tile,
                # compare its histogram with sample histogram set to find the best match
                compare = comparison(bins, option)
                temp = [tile] # input should be a list
                targetHist  = compare.hist_set(temp)
                sampleHists = compare.hist_set(sampleSet)
                match = compare.compare_hist(targetHist[0], sampleHists)
                # replace each tile with the best fit image
                croppedImg[row:row + self.height, col:col + self.width] = sampleSet[match]

        # generate the filtered image
        cv2.imwrite(outputDir, croppedImg)

class comparison:
    '''
    Compares the color difference between two images based on their RGB histogram.
    '''
    def __init__(self, bins, option):
        self.bins = bins
        self.option = option

    def generate_hist(self, img):
        '''
        Generates 3D RGB histogram and normalizes it.
        '''
        hist = cv2.calcHist([img], [0, 1, 2], None, [self.bins, self.bins, self.bins], [0, 256, 0, 256, 0, 256])
        cv2.normalize(hist, hist)
        return hist.flatten()

    def hist_set(self, sampleSet):
        '''
        Generates a list of histograms.
        '''
        histSet = []
        for sample in sampleSet:
            histSet.append(self.generate_hist(sample))

        return histSet

    def compare_hist(self, tarHist, sampleHistSet):
        '''
        Computes the differences between the target histogram and histograms of the sample set.
        '''
        methods = {
            "correlation" : cv2.HISTCMP_CORREL,         # Correlation
            "chi-squared" : cv2.HISTCMP_CHISQR,         # Chi-Squared
            "intersection" : cv2.HISTCMP_INTERSECT,     # Intersection
            "hellinger" : cv2.HISTCMP_BHATTACHARYYA}    # Hellinger

        # results should be in reverse order
        # when applying Correlation and intersection method
        rev = False
        if self.option in ("correlation",  "Hellinger"):
            rev = True

        results = {}
        for i in range(0, len(sampleHistSet)):
            diff = cv2.compareHist(tarHist, sampleHistSet[i], methods[self.option])
            results[i] = diff       
        results = sorted([(v, k) for (k, v) in results.items()], reverse = rev)

        # retrive the index of the best matched sample
        return results[0][1]

# main() function
def main():
    # create parser
    descStr = "This program applies mosaic filter onto the image specified."
    parser = argparse.ArgumentParser(description=descStr)
    # add expected arguments
    parser.add_argument('--i', dest='targetFile', required=True)
    parser.add_argument('--sample', dest='sampleFile', required=False)
    parser.add_argument('--type', dest='fileType', required=False)
    parser.add_argument('--height', dest='height', required=False)
    parser.add_argument('--width', dest='width', required=False)
    parser.add_argument('--o', dest='outFile', required=False)
    parser.add_argument('--bins', dest='bins', required=False)
    parser.add_argument('--opt', dest='option', required=False)

    # parse args
    args = parser.parse_args()

    targetFile = args.targetFile        # path to the target file
    sampleFile = "./color_set"          # path to the sample set
    if args.sampleFile:
        sampleFile = args.sampleFile
    fileType = ".jpg"                   # type of the image in the sample set
    if args.fileType:
        fileType = args.fileType
    height = 16                         # height of the tile
    if args.height:
        height = int(args.height)
    width = 16                          # width of the tile
    if args.width:
        width = int(args.width)
    outFile = "./out.jpg"               # path to the output file
    if args.outFile:
        outFile = args.outFile
    bins = 8                            # number of bins used for calculating RGB histogram
    if args.bins:
        bins = int(args.bins)
    option = "correlation"              # method used for calculating histogram differences
    if args.option:
        option = args.option

    targetImg = imgProcess(targetFile, sampleFile, fileType, height, width)
    targetImg.mosaic(outFile, bins, option)

# call main
if __name__ == '__main__':
    main()
