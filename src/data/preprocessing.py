import numpy as np
import matplotlib.pyplot as plt


def prevalence_threshold(df, threshold=0.5):
    '''
    PURPOSE:
        Take a (samples x features) dataframe and return only
        features present in fraction of samples > the threshold
    INPUT:
        df - pandas dataframe (samples x features)
    OUTPUT:
        output - dataframe containing only the columns (features)
            that pass the prevlaence threshold
    '''

    print "Requiring sample to be present in %s percent of samples" % threshold
    test = ((df > 1e-20).sum(axis=0) / df.shape[0]) >= threshold
    output = df[df.columns[test]]
    return output


def correct_dilution_factor(X, plot=False):
    '''
    GOAL:
        Correct for systematically biased intensity values
        by finding a dilution factor (if the median of
        feature mean-intensities is high, your sample is too concentrated)
    INPUT:
        X - (samples x features) dataframe
        plot - whether or not to plot histogram of dilution factors
    OUTPUT:
        X_pqn - Dataframe (samples x features)
            normalized by dilution factor
    '''
    feature_means = np.mean(X, axis=0)
    # mean-center each feature
    X_mean_centered = np.divide(X, feature_means[np.newaxis, :])
    # ignore the nans when calculating median
    dilution_factors = np.nanmedian(X_mean_centered, axis=1)
    if plot:
        plt.hist(dilution_factors, bins=50)
        plt.title('Dilution factor distribution')
        plt.show()
    # broadcast correctly to divide column-wise
    X_pqn = np.divide(X, dilution_factors[:, np.newaxis])
    return X_pqn
#
