'''
By: Ang Li
'''
import argparse
import cv2
import os
import re

class imgProcess:
    def __init__(self, targetDir, sampleDir, fileType, height, width):
        '''
        targetDir:      path to the target image
        sampleDir:      path to the directory containing sample images
        height & with:  size of the cropped sample image,
                        also used as the size of the tile in the mosaic painting
        '''
        self.targetDir = targetDir
        self.sampleDir = sampleDir
        self.fileType = fileType
        self.height = height
        self.width= width

    def load_samples(self):
        '''
        Loads sample images and CROPS them to the size specified.
        '''
        sampleSet = []

        for filename in os.listdir(self.sampleDir):
            # validate the file type
            if not re.search(self.fileType, filename, re.I):
                continue
            filepath = os.path.join(self.sampleDir, filename)

            # open and crop the sample to the size specified
            img = cv2.imread(filepath)
            h, w = img.shape[:2]
            if h < self.height or w < self.width:
                print("Failed to crop " + filename + ": out of the boundary.")
                continue
            sampleSet.append(img[0:self.height, 0:self.width].copy()) # only keep the crops in the memory

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
    https://www.pyimagesearch.com/2014/07/14/3-ways-compare-histograms-using-opencv-python/
    https://www.pyimagesearch.com/2014/01/22/clever-girl-a-guide-to-utilizing-color-histograms-for-computer-vision-and-image-search-engines/
    https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_histograms/py_histogram_begins/py_histogram_begins.html
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
    targetFile = args.targetFile
    sampleFile = "./color_set"
    if args.sampleFile:
        sampleFile = args.sampleFile
    fileType = ".jpg"
    if args.fileType:
        fileType = args.fileType
    height = 16
    if args.height:
        height = int(args.height)
    width = 16
    if args.width:
        width = int(args.width)
    outFile = "./out.jpg"
    if args.outFile:
        outFile = args.outFile
    bins = 8
    if args.bins:
        bins = int(args.bins)
    option = "correlation"
    if args.option:
        option = args.option

    targetImg = imgProcess(targetFile, sampleFile, fileType, height, width)
    targetImg.mosaic(outFile, bins, option)

# call main
if __name__ == '__main__':
    main()
