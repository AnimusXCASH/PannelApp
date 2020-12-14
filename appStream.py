import streamlit as st
from api_access import SolarCheck
from datetime import datetime
from datetime import timedelta
import pandas as pd
import base64
from io import BytesIO
from functools import reduce
from datetime import date

# Configure page
st.set_page_config(page_title='The boss', page_icon="🔌", layout='wide', initial_sidebar_state='expanded')


def process_meters(metering_points: dict):
    """
    Porcessing all the meters availabale under the owners account
    :param metering_points:
    :return:
    """
    for m in metering_points:
        st.header(f"Metering point ID: {m['meteringPointId']}")
        col1, col2 = st.beta_columns([1, 1])
        col1.subheader("Metering point details:")
        col1.text(f"Product Type: {m['productType']}\n"
                  f"Metering Point Type: {m['meteringPointType']}\n"
                  f"Meter Numbers: {m['meterNumber']}")
        col2.subheader("Available Channels")
        col2.dataframe(m["channels"])


def welcome_string():
    """
    Loads on start with explanation
    :return:
    """
    st.balloons()
    st.title("Welcome to the Solar Panel Explorer")
    st.subheader("How to start?")
    st.info("Go to sidebar on the left side and choose from drop down menu LOGIN. Provide credential details and if "
            "account found, you will be automatically logged in after putting a tick into login box.")


def successfull_login_info():
    st.title("Account Explorer")
    st.markdown("Below is the information on all available sections accessible through __Account Menu__ drop-down in"
                " sidebar. They were designed to allow access to information on your ***metering points*** and their "
                "***statistics*** in sections for ***day*** and ***_month_***.\n"
                "\n## :thermometer: Metering Points\n")
    st.info("Returns information on all available metering points currently connected to this account."
            " Details such as __id__, __type__, __channels list with characteristics__ are returned.")

    st.markdown("\n## :bar_chart: Statistics\n")
    st.info(" Statistical information per each accessible ***__Metering Point ID__*** is returned based on "
            "pre selected timeframe. Available timeframes are ***__Daily__*** and ***__Monthly__***."
            " Furthermore statistical data per either channel or merged with all showcased channels is available"
            " to be downloaded in __csv__ or __excel__ file.\n")
    st.markdown("\n## :house: Home\n")
    st.info("Return to this page.\n")


def download_link(file_to_download, file_name: str, button_text: str, file_type: str):
    """
    Create a link to download specific dataframe
    :param file_to_download:
    :param file_name:
    :param button_text:
    :return:
    """

    if isinstance(file_to_download, pd.DataFrame):
        if file_type == 'csv':
            file_to_download = file_to_download.to_csv(index=True)
            b64 = base64.b64encode(file_to_download.encode()).decode()
            return f'<a href="data:file/txt;base64,{b64}" download="{file_name}">{button_text}</a>'
        elif file_type == 'xls':
            val = dataframe_to_excel(file_to_download)
            b64 = base64.b64encode(val)  # val looks like b'...'
            return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="Your_File.xlsx">Download Excel file</a>'  # decode b'abc' => abc


def dataframe_to_excel(data_frame, sheet_name: str = None):
    """
    Stores the dataframe to excel for export
    :param data_frame: pd.DataFrame
    :param sheet_name: Name of the sheet in excel file
    :return:
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data_frame.to_excel(writer, index=True, sheet_name=f'{sheet_name}')
    workbook = writer.book
    worksheet = writer.sheets[f'{sheet_name}']
    format1 = workbook.add_format({'num_format': '0.00'})  # Tried with '0%' and '#,##0.00' also.
    worksheet.set_column('A:A', None, format1)  # Say Data are in column A
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def produce_total_windows(dataframe: pd.DataFrame):
    """
    Produce the UX for all data on one chart
    :param dataframe: Pandas Dataframe
    :return: None
    """
    pos1, pos2, pos3 = st.beta_columns([3, 1, 0.5])
    pos1.line_chart(dataframe)
    column_names = list(dataframe.keys())
    for name in column_names:
        pos2.markdown(f'{name} total: {dataframe[name].sum()} ')
    pos2.dataframe(dataframe)
    if pos3.button(f"Get CSV"):
        tmp_download_link = download_link(dataframe, f'YOUR_DF.csv', 'Click here to download your data!',
                                          file_type='csv', )
        pos3.markdown(tmp_download_link, unsafe_allow_html=True)
    elif pos3.button(f"Get Xls"):
        tmp_download_link = download_link(dataframe, 'YOUR_DF.csv', 'Click here to download your data!',
                                          file_type='xls')
        pos3.markdown(tmp_download_link, unsafe_allow_html=True)


def produce_data_window(dataframe, id: str, meter_unit: str):
    """
    Produce UX
    :param dataframe: Pandas dataframe
    :param id: Id of the meter
    :param meter_unit: Unit used for channel
    :return: None
    """
    pos1, pos2, pos3 = st.beta_columns([4, 1, 0.5])
    pos1.line_chart(dataframe)
    pos2.markdown(f'Total: {dataframe[f"{id}"].sum()} {meter_unit}')
    pos2.write(dataframe)
    if pos3.button(f"Get {id} CSV"):
        tmp_download_link = download_link(dataframe, 'YOUR_DF.csv', 'Click here to download your data!',
                                          file_type='csv', )
        st.markdown(tmp_download_link, unsafe_allow_html=True)
    elif pos3.button(f"Get {id} Xls"):
        tmp_download_link = download_link(dataframe, 'YOUR_DF.csv', 'Click here to download your data!',
                                          file_type='xls')
        st.markdown(tmp_download_link, unsafe_allow_html=True)


def process_points(ids: list, solar, connection_id, month=None, year=None, selected_date=None,
                   monthly: bool = False) -> list:
    """
    Filters all the points available
    :param ids: Point Ids
    :param solar: Solar Class to access class functions
    :param connection_id: Id as int
    :param month: month
    :param year: year
    :param selected_date: selection box
    :param monthly: Boolean if monthly stats are for processing
    :return: List of processed data
    """
    new_structure = list()
    for id in ids:
        if not monthly:
            id_values = solar.get_daily(connection_id, id["meteringPointId"], selected_date.year, selected_date.month,
                                        selected_date.day)
        else:
            id_values = solar.get_monthly(connection_id, id["meteringPointId"], year, month)
        if isinstance(id_values, dict):
            id['stats'] = id_values
            new_structure.append(id)
    return new_structure


def make_new_dictionary(old_one: dict):
    """
    Creates new dictionary from the old one as some key poping is needed
    :param old_one:
    :return:
    """
    new_structure = dict()
    for k in old_one.keys():
        try:
            if isinstance(int(k), int):
                pass
        except ValueError:
            new_structure[k] = old_one[k]
    return new_structure


def get_channel_details(metering_points: list, metering_point_id: str, channel_id: str):
    """
    Get  just the details of the channel which is used for data presentation
    :param metering_points: List of all metering points
    :param metering_point_id: id of the metering point used in a call
    :param channel_id: Id of the channel to be queried for the history
    :return: channel details in form of:
    {
    "channel":"18160"
    "unit":"KW"
    "direction":"LVR"
    }
    """
    for point in metering_points:
        if point["meteringPointId"] == metering_point_id:
            for channel in point["channels"]:
                if channel["channel"] == channel_id:
                    return channel


def process_stats(data: list) -> list:
    """
    Process stats to filter out just the ones needed and construct new structure for processing
    :param data: list of all the stats from API
    :return: Restructured stats
    """
    new_structure = list()
    # Process every meter
    for meter in data:
        new_meter = dict()
        # Process meter point
        stats = meter["stats"]
        # take out just the ones needed in list from 1020, 16080
        for k in stats.keys():
            new_stats = dict()
            if int(k) in [10280, 16080]:
                new_stats[f'{k}'] = stats[f'{k}']

        new_meter = {key: value for d in (new_stats, meter) for key, value in d.items()}
        updated_meter = make_new_dictionary(old_one=new_meter)
        new_structure.append(updated_meter)
    return new_structure


def main():
    """
    Main entry for the program to run
    :return: None
    """
    # Available menu entries
    entry_menu = ["Home", "Login"]
    menu_choice = st.sidebar.selectbox("Menu", entry_menu)

    if menu_choice == "Home":
        welcome_string()

    elif menu_choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.checkbox("Login"):
            # Check the account status through ping
            solar = SolarCheck(username, password)
            account_data = solar.get_all_meters()
            if account_data[0]:
                # Sub menu after log in
                logged_in_menu = ["Home", "Metering Points", "Statistics"]
                st.sidebar.text("Select option:")
                action = st.sidebar.selectbox("Account Menu", logged_in_menu)

                # Loading required data
                connection_details = account_data[1][0]  # Get all metering points attached under the account
                connection_id = connection_details["connectionId"]  # get connection id
                metering_points = connection_details["meteringPoints"]  # Get list of metering point
                ids = solar.process_mettering_points(
                    metering_points)  # Get IDs and channels of each mettering point in array

                # Start processing menu selections
                if action == "Home":
                    successfull_login_info()
                if action == "Metering Points":
                    process_meters(metering_points)

                elif action == "Statistics":
                    menu = ["Daily", "Monthly"]
                    choice = st.sidebar.selectbox("Time Frame", menu)
                    if choice == "Daily":
                        st.markdown(f"Connection ID **__{connection_id}__**")
                        today = datetime.today() - timedelta(1)
                        date_selection = st.sidebar.date_input("Choose date to where you want to retrieve data from",
                                                               today)
                        if not date_selection >= date.today():
                            merged_dataframes = list()
                            st.text(
                                f'Getting data for {date_selection.day}.{date_selection.month}.{date_selection.year}')
                            data_expaned_stats = process_points(ids, solar, connection_id, selected_date=date_selection)
                            final_data = process_stats(data_expaned_stats)
                            for point in final_data:
                                st.markdown(f"*** :sparkles: Data for Metering point ID {point['meteringPointId']}***")
                                filtered = [x for x in point['stats'].keys() if int(x) in [10280, 16080]]
                                for chn_stats_cat in filtered:
                                    channel_details = get_channel_details(metering_points=metering_points,
                                                                          metering_point_id=point['meteringPointId'],
                                                                          channel_id=chn_stats_cat)
                                    st.write(f"No: {channel_details['channel']}")
                                    st.write(f"Direction:{channel_details['direction']}\n")
                                    st.write(f"Unit:{channel_details['unit']}")
                                    dataframe = solar.make_data_frame(data=point['stats'][chn_stats_cat],
                                                                      column_name=chn_stats_cat)
                                    produce_data_window(dataframe=dataframe, id=chn_stats_cat,
                                                        meter_unit=channel_details['unit'])
                                    merged_dataframes.append(dataframe)  # Append to list for futher analywsis

                            st.markdown(f"*** :sparkles: Summary ***")
                            all_together = reduce(lambda df_left, df_right: pd.merge(df_left, df_right,
                                                                                     left_index=True, right_index=True,
                                                                                     how='outer'), merged_dataframes)

                            produce_total_windows(dataframe=all_together)
                        else:
                            st.error("Please selected date which is older than today!")

                    elif choice == "Monthly":
                        st.markdown(f"Connection ID **__{connection_id}__**")
                        pos_month, pos_year = st.sidebar.beta_columns([1, 1])
                        today = datetime.today()
                        month_options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
                        selected_month = pos_month.selectbox(label='Month',
                                                            options=month_options, index=month_options[today.month - 2])
                        selected_year = pos_year.selectbox(label='Year', options=[2020, 2021, 2022])

                        if selected_month <= today.month and selected_year <= today.year:
                            merged_dataframes = list()
                            st.text(f'Getting data {selected_month}.{selected_year}')
                            data_expaned_stats = process_points(ids, solar, connection_id, selected_month,
                                                                selected_year,
                                                                monthly=True)
                            final_data = process_stats(data_expaned_stats)
                            for point in final_data:
                                st.markdown(f"*** :sparkles: Data for Metering point ID {point['meteringPointId']}***")
                                filtered = [x for x in point['stats'].keys() if int(x) in [10280, 16080]]
                                for chn_stats_cat in filtered:
                                    channel_details = get_channel_details(metering_points=metering_points,
                                                                          metering_point_id=point['meteringPointId'],
                                                                          channel_id=chn_stats_cat)
                                    st.write(f"No: {channel_details['channel']}")
                                    st.write(f"Direction:{channel_details['direction']}\n")
                                    st.write(f"Unit:{channel_details['unit']}")
                                    dataframe = solar.make_data_frame(data=point['stats'][chn_stats_cat],
                                                                      column_name=chn_stats_cat)
                                    produce_data_window(dataframe=dataframe, id=chn_stats_cat,
                                                        meter_unit=channel_details['unit'])
                                    merged_dataframes.append(dataframe)  # Append to list for futher analywsis

                            st.markdown(f"*** :sparkles: Merged Data ***")
                            all_together = reduce(lambda df_left, df_right: pd.merge(df_left, df_right,
                                                                                     left_index=True, right_index=True,
                                                                                     how='outer'), merged_dataframes)

                            produce_total_windows(all_together)
                        else:
                            st.title("Get back to present or past")

            else:
                error_details = account_data[1]
                st.warning(f"{error_details['title']} or {error_details['type']} access")


if __name__ == "__main__":
    main()
