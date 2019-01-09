# This is the script pydoit
# will call to run all your analysis
# Assumes that input are feature tables from
# xcms
import pandas as pd
from sklearn import preprocessing


class Xcms_organize():

    def __init__(self, data_path):
        # Load the data and parse it a bit
        self.data_path = data_path
        self.all_data = pd.read_csv(self.data_path,
            sep='\t', index_col=0)
        # index with mzrt
        mz = self.all_data.loc[:, 'mz'].astype('str')
        rt = self.all_data.loc[:, 'rt'].astype('str')
        idx = mz+':'+rt
        self.all_data.index = idx
        # Get feature table by removing first 8 columns
        # these contain stuff like mzmin/max, rtmin/max,
        # assay name, and number of peaks
        # TODO sort this
        self.feature_table = (self.all_data.iloc[:,8:]
                                .sort_index(axis=1)).T
        if self.feature_table.shape[0] > self.feature_table.shape[1]:
            print("Do you really have more samples (rows) than features (col)?")


    def mtbls_class_mapping(self, a_path, s_path,
            class_label_col):
        # a_path: path to a_*.txt file - assay info
        # s_path: path to s_*.txt file - sample info
        # class_label_col: the label of column in s_*.txt
        #   That contains class_labels
        self.assay_info = pd.read_csv(a_path, sep='\t')
        self.sample_info = pd.read_csv(s_path, sep='\t')
        self.sample_info.set_index('Sample Name', inplace=True,
                drop=False)
        self.assay_info.set_index('Sample Name', inplace=True,
                drop=False)
        # Catch if the class-label column isn't there'
        # and inform user why
        try:
            s_info = self.sample_info[
                        ['Source Name', 'Sample Name', class_label_col]]
        except KeyError as error:
            print(('Error is likely b/c The class label column, "{col}"'
                   ' wasnt found in {path}').format(col=class_label_col,
                       path=s_path))
            raise
        a_info = self.assay_info[['MS Assay Name',
                'Raw Spectral Data File']]
        self.sample_map = pd.concat([s_info, a_info], axis=1)
        self.class_label_col = class_label_col
        # Now find the column in sample_map
        # that has all the sample names in it
        sample_names = self.feature_table.index
        sample_col = None
        for col in self.sample_map.iteritems():
            num_matches = (self.sample_map[col[0]] == sample_names).sum()
            if num_matches == len(sample_names):
                sample_col = col[0]
                break
        if sample_col == None:
            raise ValueError('No perect match found for all'
                ' sample names in the feature table.'
                '\n\nDid you make sure to remove any annoying'
                ' xcms prefixes (usually "X") with'
                ' .remove_column_prefix()?'
                '\n\nOtherwise check self.sample_map to figure'
                ' out which column of "sample_map"'
                'contains the sample names')
        else:
            self.sample_col = sample_col
            self.sample_classes = self.sample_map[[class_label_col,
                sample_col]].sort_values(sample_col)

        # make dictionary of class labels to sample names
        # {'label': [sample_1, 2, ..]}
        classes = self.sample_classes[self.class_label_col].unique()
        self.class_dict = {}
        for label in classes:
            # get all the entries that have particular class labe
            class_vals = (self.sample_classes[self.sample_classes[self.class_label_col] == label])
            # get all the sample names that have that class label
            self.class_dict[label] = class_vals[self.sample_col].values


    def class_encoder(self):
        # make sure that the feature table is
        # same order as the class labels
        assert(self.sample_classes[self.sample_col]
                == self.feature_table.index).all()
        le = preprocessing.LabelEncoder()
        self.y = le.fit_transform(
            self.sample_classes[self.class_label_col]
            )
        print(('Were you expecting {n} classes?'
              ' because thats how many you have.'
              ' look at self.sample_classes if this is'
              ' unexpected').format(n=len(set(
                  self.sample_classes[self.class_label_col])))
              )

    def remove_column_prefix(self, prefix='X'):
        # if all columns are X1001, X1002, instead of
        # 1001, 1002, because xcms did some dumbass shit,
        # use this fxn to remove those X's from column names

        # First, assert that prefix is first character in all
        # columns
        if (sum(
                [prefix == string[0:len(prefix)]
                   for string in self.feature_table.index])
                ==
                self.feature_table.shape[0]) is not True:

            raise ValueError(('The column prefix you gave isnt present'
                ' in all columns of the feature_table'))

        new_cols = [col[len(prefix):]
                       for col in self.feature_table.index
                    ]
        self.feature_table.index = new_cols


    # These might be easier to do in R, since IHW is already implemented
    # and I have sample code
    def mann_whitney(self):
        # run mann-whitney on all features
        # for the different classes
        pass


    def scatterplot_pvals(self, pvals, covariate):
        # scatterplot the -log10(pvals) with a covariate,
        # like mean/median intensity, m/z, rt, intensity variance
        pass


def encode_new_classes(class_dict):
    # {'class-label': [sample_name1, sample_name2, ...]
    lst = []
    for k in class_dict.keys():
        s = pd.Series(class_dict[k], name=k)
        lst.append(s)
    # do some reshaping to get a series of class labels,
    # indexed by sample ID (which is the index of feature table)
    df = (pd.concat(lst, axis=1)
       .melt()
       .dropna(how='any')
       .set_index('value')
       .sort_index()
     )
    return df

# preprocessing
# case v. control intensity hists before and after preprocess
# dilution correction, filtering samples
# variance filter?


# Repeat the data examination stuff
# with filtered data..?


# regular-old RF classification-cv

# RF classifier at different time-slices

#
