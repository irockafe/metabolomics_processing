import pandas as pd


def factors_to_df(mwtfile):
    '''
    GOAL - convert from the gross '|' delimited metadata to a nice dataframe
    INPUT - mwtfile file
    OUTPUT - pandas dataframe of metadata (samples x factors)
    TODO - Make this tidy?
    '''
    sample_names = (mwtfile['MS_METABOLITE_DATA']['MS_METABOLITE_DATA_START']
                    ['Samples'])
    metadata = (mwtfile['MS_METABOLITE_DATA']['MS_METABOLITE_DATA_START']
                ['Factors'])
    metadata_nested_dict = {}
    for i in range(0, len(metadata)):
        lst = metadata[i].split(' |')
        dct = {}
        for j in lst:
            dct[j.split(':')[0]] = j.split(':')[1]
        metadata_nested_dict[sample_names[i]] = dct
    df = pd.DataFrame(metadata_nested_dict).T
    return df.sort_index()


def get_feature_table(mwtfile):
    '''
    GOAL: Get the feature table from mwtfile file
    INPUT: mwtfile file
    OUTPUT: pandas dataframe of feature table (samples x features)
    '''
    df = (pd.DataFrame(mwtfile['MS_METABOLITE_DATA']
                       ['MS_METABOLITE_DATA_START']
                       ['DATA'], dtype='float64')
            .set_index('metabolite_name')
            .T)
    print ("you'll probably have to conver this dataframe to float after you" +
           "replace null values")
    return df.sort_index()

#
