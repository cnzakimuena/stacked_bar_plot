"""
Preprocessing class for handling data manipulation and analysis.
"""


class Preprocessor:
    """
    The class provides methods for preprocessing data for visualization. It includes functionality 
    for handling both location-based and time-based binning of data, as well as calculating 
    proportional inputs for stacked bar plots. The class is designed to be used for the electricity 
    production dataset. It could be adapted to other datasets and preprocessing needs.
    """

    def __init__(self, data_df, global_variable, group_variable):

        self.data_df = data_df
        self.global_variable = global_variable
        self.group_variable = group_variable
        self.sub_data_df = None
        self.bin_num = None
        self.bin_names_list = None
        self.global_value = None
        self.group_variable_list = None
        self.dependent_input = None
        self.percentage_input = None
        self.selected_input = None
        self.dependent_variable_label = None
        # location version-specific assignments
        self.global_variable_list = None
        # time version-specific assignments
        self.group_list = None
        self.group_ranges = None

    @staticmethod
    def is_continuous(lst):
        """
        Determine if a list of values is continuous (i.e., forms a sequence without gaps).
        """
        if not lst:
            raise ValueError("List is empty")
        # condition max - min + 1 == length and no duplicates
        return (max(lst) - min(lst) + 1 == len(lst)) and (len(set(lst)) == len(lst))

    @staticmethod
    def modify_column_names(df, new_column_names, target_column_indices):
        """ 
        Modify column names of a DataFrame based on provided new names and their corresponding 
        indices.
        """
        df = df.copy()
        # create a mapping: {current_name_at_index: new_name}
        mapping = {df.columns[i]: new_column_names[j] \
            for j, i in enumerate(target_column_indices)}
        # apply modification
        df.rename(columns=mapping, inplace=True)
        return df

    def aggregate_groups(self, constant_cols, sum_cols, agg_col):
        """
        Aggregate data by grouping based on a specified column. For columns in constant_cols, the 
        last value in each group is retained. For columns in sum_cols, values are summed within 
        each group.
        """
        # aggregation dictionary
        agg_strategy = {col: 'last' for col in constant_cols}
        agg_strategy.update({col: 'sum' for col in sum_cols})
        # apply to groupby
        self.sub_data_df = self.sub_data_df.groupby(agg_col, as_index=False).agg(agg_strategy)

    def get_proportional_input(self):
        """ 
        Calculate the proportional input for each dependent variable by dividing each value by the 
        sum of the corresponding group. The result is then converted to a percentage.
        """
        # get sum list of lists
        sum_list = [None] * self.bin_num
        for t in range(self.bin_num):
            sum_list[t] = sum(sublist[t] for sublist in self.dependent_input)
        # divide each dependent input sublist by sum list element-wise
        fraction_input = \
            [[item / div for item, div in zip(sub, sum_list)] for sub in self.dependent_input]
        # convert to percentage
        self.percentage_input = \
            [[item * 100 for item in sublist] for sublist in fraction_input]

    def get_dependent_inputs(self, preprocessing_type, **kwargs):
        """
        Gather dependent inputs based on the specified preprocessing type. The method supports both
        location-based and time-based binning of data. Depending on the preprocessing type, the 
        method will call the appropriate helper functions to process the data and calculate the 
        dependent inputs. The method also handles the assignment of bin names and group variable 
        lists as needed.
        """
        # gather absolute and proportional dependent inputs
        if preprocessing_type == 'location_bins' and \
            'global_variable_list' in kwargs and 'group_variable_range' in kwargs:
            self.bin_names_list = kwargs['global_variable_list']
            self.group_variable_list = list(range(kwargs['group_variable_range'][0],
                                                  kwargs['group_variable_range'][1] + 1))
            self.bin_num = len(kwargs['global_variable_list'])
            self.get_dependent_inputs_location()
        elif preprocessing_type == 'time_bins' and \
            'bin_num' in kwargs and 'global_value' in kwargs:
            # define selected bin
            self.bin_num = kwargs['bin_num']
            # define global value
            self.global_value =  kwargs['global_value']
            if 'group_variable_range' in kwargs:
                self.group_variable_list = list(range(kwargs['group_variable_range'][0],
                                                      kwargs['group_variable_range'][1] + 1))
            self.get_dependent_inputs_time()

    def select_input(self, input_string):
        """ 
        Select the input to be used for plotting based on the provided input string. The method
        assigns the selected input and sets the corresponding dependent variable label. The input 
        string can be either 'dependent_input' for absolute values or 'percentage_input' for 
        relative values.
        """
        if input_string == 'dependent_input':
            self.selected_input = self.dependent_input
            self.dependent_variable_label = 'Electricity production [TWh]'
        elif input_string == 'percentage_input':
            self.selected_input = self.percentage_input
            self.dependent_variable_label = 'Relative\nelectricity production [%]'
        elif self.dependent_variable_label is None:
            raise ValueError("Dependent_variable label is None.")

    # --- preprocessing (location bins) ---

    def get_df_subset_location(self):
        """ 
        Obtain a subset of the original DataFrame based on the specified global variable list and 
        group variable list.
        """
        # select subset
        self.sub_data_df = \
            self.data_df[self.data_df[self.global_variable].isin(self.bin_names_list) & \
                self.data_df[self.group_variable].isin(self.group_variable_list)].copy()

    def get_dependent_inputs_location(self):
        """ 
        This method processes the data for location-based binning. It first obtains a subset of the
        original DataFrame based on the specified global variable list and group variable list. If 
        the group variable list contains more than one value, the method aggregates the data based 
        on the dependent variable. The method then converts the relevant columns of the subset 
        DataFrame into individual lists and combines them into a list of lists for the dependent 
        input. Finally, the method calculates the proportional dependent input for use in relative 
        stacked bar plots.
        """
        self.get_df_subset_location()
        # if group variable list is greater than 1, aggregate based on dependent variable
        if len(self.group_variable_list) > 1:
            # define constant and sum columns
            constant_cols = self.sub_data_df.columns.tolist()[:3]
            sum_cols = self.sub_data_df.columns.tolist()[3:]
            self.aggregate_groups(constant_cols, sum_cols, self.global_variable)
        # convert relevant columns to individual lists and combine as list of lists
        self.dependent_input = self.sub_data_df.iloc[:, 3:].T.values.tolist()
        # gather proportional dependent input
        self.get_proportional_input()

    # --- preprocessing (time bins) ---

    def get_group_ranges(self, list_length):
        """ 
        Gather group ranges for time-based binning based on the specified number of bins and the 
        length of the group variable list. The method calculates the size of each group and creates 
        a list of tuples representing the start and end indices for each group.
        """
        # from length integer and number of groups, returns ranges of equal lengths
        if self.bin_num <= 0:
            raise ValueError("Number of groups must be greater than 0.")
        if list_length < self.bin_num:
            raise ValueError("List length must be >= number of groups.")
        # calculate the strict equal size for each group
        group_size = list_length // self.bin_num
        self.group_ranges = []
        start_idx = 0
        for _ in range(self.bin_num):
            end_idx = start_idx + group_size
            self.group_ranges.append((start_idx, end_idx))
            start_idx = end_idx  # move to the next start position

    def add_binning_column(self):
        """ 
        Add a binning column to the subset DataFrame based on the group ranges calculated for 
        time-based binning.
        """
        # obtain binning column
        bin_list = [None] * len(self.sub_data_df)
        for group_ranges_index, current_group_range in enumerate(self.group_ranges):
            group_range_start, group_range_end = current_group_range
            bin_list[group_range_start:group_range_end] = \
                [group_ranges_index] * (group_range_end - group_range_start)
        # add binning column to data frame
        self.sub_data_df['bin'] = bin_list

    def get_bin_names_time(self):
        """ 
        Obtain bin names for time-based binning based on the group ranges and the group variable 
        list. The method creates a list of bin names by checking the values in the group variable 
        list that correspond to the start and end indices of each group range.     
        """
        self.bin_names_list = [None] * self.bin_num
        for group_ranges_index, _ in enumerate(self.group_ranges):
            if str(self.group_list[self.group_ranges[group_ranges_index][0]]) == \
                str(self.group_list[self.group_ranges[group_ranges_index][1]-1]):
                self.bin_names_list[group_ranges_index] = \
                    str(self.group_list[self.group_ranges[group_ranges_index][0]])
            else:
                self.bin_names_list[group_ranges_index] = \
                    str(self.group_list[self.group_ranges[group_ranges_index][0]]) + '-' \
                        + str(self.group_list[self.group_ranges[group_ranges_index][1]-1])

    def get_dependent_inputs_time(self):
        """ 
        This method processes the data for time-based binning. It first obtains a subset of the 
        original DataFrame based on the specified global value and group variable list.
        The method then calculates the group ranges for binning based on the specified number of 
        bins and the length of the group variable list. A binning column is added to the subset 
        DataFrame based on the group ranges, and the data is aggregated based on the binning 
        column. The relevant columns of the subset DataFrame are converted into individual lists 
        and combined into a list of lists for the dependent input. Finally, the method calculates 
        the proportional dependent input for use in relative stacked bar plots.
        """
        # get subset dataframe based on location
        if self.group_variable_list is not None:
            self.sub_data_df = \
                self.data_df[(self.data_df[self.global_variable] == self.global_value) & \
                    (self.data_df[self.group_variable].isin(self.group_variable_list))].copy()
        elif self.group_variable_list is None:
            self.sub_data_df = \
                self.data_df[self.data_df[self.global_variable] == self.global_value].copy()
        # proceed only if group values are continuous
        self.group_list = self.sub_data_df[self.group_variable].to_list()
        if self.is_continuous(self.group_list) is False:
            raise ValueError("Group values are not continuous")
        # obtain group variable binning ranges
        self.get_group_ranges(len(self.sub_data_df))
        # add binning column
        self.add_binning_column()
        # obtain aggregated groups data based on bin column
        # define constant and sum columns
        constant_cols = self.sub_data_df.columns.tolist()[:3]
        sum_cols = self.sub_data_df.columns.tolist()[3:-1]
        self.aggregate_groups(constant_cols, sum_cols, 'bin')
        # gather dependent input
        # convert relevant columns to individual lists and combine as list of lists
        self.dependent_input = self.sub_data_df.iloc[:, 4:].T.values.tolist()
        # gather proportional dependent input
        self.get_proportional_input()
        # gather bin names
        self.get_bin_names_time()
