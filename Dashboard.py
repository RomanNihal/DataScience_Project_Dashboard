import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from rapidfuzz import process

st.set_page_config(page_title="Donation Dashboard", layout="wide")
st.title("🎯 Donation Insight Dashboard")

# --- File Upload ---
upload_file = st.sidebar.file_uploader("📤 Upload CSV File", type='csv')
if upload_file is not None:
    df = pd.read_csv(upload_file)

    # -------------------------------------------------------------------- Preprocessing -------------------------------------------------------------
    currency = "BDT" if "bdt" in upload_file.name.lower() or "bangladesh" in upload_file.name.lower() else "USD"
    amount_col = [col for col in df.columns if "donation amount" in col.lower()][0]

    df['Email'] = df['Email'].fillna('No email provided').str.lower().str.strip()
    df['Donation Type'] = df['Donation Type'].str.strip().str.capitalize()
    df['Project'] = df['Project'].str.replace(r'\s+', ' ', regex=True).str.strip().str.title()

    valid_projects = ['Orphan Children', 'Feed the Hungry', 'Homeless Shelter', 'Medical Aid',
                      'Back to School Kits', 'Rohingya Refugee Support', 'Medical Care', 'Eid Gifts For Children']
    df['Project'] = df['Project'].apply(lambda x: process.extractOne(x, valid_projects)[0] if process.extractOne(x, valid_projects)[1] > 80 else x)

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.drop_duplicates()
    df['Month'] = df['Date'].dt.month
    df = df[df[amount_col] <= df[amount_col].quantile(0.95)]
    df['Phone'] = df['Phone'].astype(str).str.replace(r'\D', '', regex=True)
    df['Phone'] = df['Phone'].apply(lambda x: f"+880{x[-10:]}" if currency == "BDT" else f"+1{x[-10:]}" if len(x) >= 10 else "Invalid")
    df['Payment Method'] = df['Payment Method'].str.strip().str.title()
    df['Payment Method'] = df['Payment Method'].apply(
        lambda x: x if x in (['Bkash', 'Nagad', 'Bank Transfer', 'Card'] if currency == "BDT"
                             else ['Card', 'Bank Transfer', 'Paypal', 'Apple Pay']) else 'Other')
    df['Notes'] = df['Notes'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    df['Location'] = df['Location'].str.title().str.strip()


    # -------------------------------------------------------------------- Side Bar -------------------------------------------------------------

    # --- Static Info ---
    st.sidebar.title("📌 About the Organization")

    st.sidebar.markdown("""
    **BASHMA Foundation** is dedicated to supporting:
    - 🧒 Orphan Children
    - 🍛 Feed the Hungry
    - 🏥 Medical Aid
    - 🎁 Eid Gifts for Children
    - 🎒 Back to School Kits
    - 🛖 Rohingya Refugee Support"""
    )

    if currency == "BDT":
        payment_methods = "**Accepted Payment Methods:** Bkash, Nagad, Bank Transfer, Card"
    else:
        payment_methods = "**Accepted Payment Methods:** Card, Bank Transfer, Paypal, Apple Pay"

    st.sidebar.markdown(payment_methods)

    st.sidebar.markdown("""
    **Donation Types**  
    - One-Time  
    - Monthly  
    - Zakat  
    - Sadaqah  
    """)

    # --- Donation Summary Metrics ---
    unique_donors = df['Donor Name'].nunique()
    donation_counts = df['Donor Name'].value_counts()
    regular_donor_count = (donation_counts > 1).sum()

    average_donation = df[amount_col].mean()

    total_donations = df[amount_col].sum()
    top_donor = df.loc[df[amount_col].idxmax()]['Donor Name']
    top_project = df['Project'].value_counts().idxmax()
    popular_method = df['Payment Method'].value_counts().idxmax()

    st.sidebar.title("📈 Quick Stats")
    st.sidebar.metric("💰 Total Donations", f"{total_donations:,.2f} {currency}")
    st.sidebar.metric("🏆 Top Donor", top_donor)
    st.sidebar.metric("📦 Top Project", top_project)
    st.sidebar.metric("💰 Average Donation", average_donation)
    st.sidebar.metric("💳 Popular Method", popular_method)


    col1, col2 = st.sidebar.columns(2)
    col1.metric("Donors", unique_donors)
    col2.metric("Regulars", regular_donor_count)



    with st.expander("📥 Export Full Cleaned Dataset"):
        # Export Entire Cleaned Dataset
        st.download_button(
            label="⬇ Download All Donations (Cleaned)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='cleaned_donations_2024.csv',
            mime='text/csv'
        )

    st.subheader("📂 Sample of the Dataset")
    st.dataframe(df.head(10))


    # -------------------------------------------------------------------- Donor Analysis -------------------------------------------------------------

    # --- Top Donors (by single donation) ---
    st.header("🏆 Top Donors by Single Donation")

    top_donations = df[['Donor Name', amount_col]].sort_values(by=amount_col, ascending=False).drop_duplicates(
        'Donor Name').head(10)

    st.dataframe(top_donations.style.format({amount_col: "{:,.2f} " + currency}))

    sns.barplot(x=top_donations[amount_col], y=top_donations['Donor Name'], palette='viridis')
    plt.title("Top 10 Donors (Single Highest Donations)")
    plt.xlabel("Donation Amount")
    plt.ylabel("Donor")
    st.pyplot(plt.gcf())
    plt.clf()

    # --- Regular Donors (donated more than once) ---
    st.header("🔁 Regular Donors")

    donation_counts = df['Donor Name'].value_counts()
    regular_donors = donation_counts[donation_counts > 1].index.tolist()
    regular_df = df[df['Donor Name'].isin(regular_donors)]

    regular_summary = regular_df.groupby('Donor Name')[amount_col].agg(['count', 'sum', 'mean']).sort_values(by='count',
                                                                                                             ascending=False)
    regular_summary.columns = ['Donation Count', 'Total Donated', 'Average Donation']

    st.dataframe(regular_summary.head(10).style.format({
        'Total Donated': "{:,.2f} " + currency,
        'Average Donation': "{:,.2f} " + currency
    }))

    # --- Loyalty Rate ---
    loyalty_rate = (len(regular_donors) / df['Donor Name'].nunique()) * 100
    st.metric("Loyalty Rate", f"{loyalty_rate:.1f}%")



    # -------------------------------------------------------------------- Project & Campaign Insights -------------------------------------------------------------

    # --- Top Funded Projects ---
    st.header("🧺 Top Funded Projects")

    top_projects = df.groupby('Project')[amount_col].sum().sort_values(ascending=False).head(5)

    sns.barplot(x=top_projects.values, y=top_projects.index, palette='Blues')
    plt.title("Highest Funded Projects")
    plt.xlabel(f"Total Donations ({currency})")
    plt.ylabel("Project")
    st.pyplot(plt.gcf())
    plt.clf()

    top_projects_df = top_projects.to_frame(name=amount_col)
    st.dataframe(top_projects_df.style.format({amount_col: "{:,.2f} " + currency}))


    # --- Donation Type Distribution ---
    st.header("💸 Donations by Type")

    donation_type_counts = df.groupby('Donation Type')[amount_col].sum()

    sns.barplot(x=donation_type_counts.index, y=donation_type_counts.values, palette='Set2')
    plt.title("Donation Type Distribution")
    plt.xlabel(f"Total Donations ({currency})")
    plt.ylabel("Donation Type")
    st.pyplot(plt.gcf())
    plt.clf()

    donation_type_counts = donation_type_counts.to_frame(name=amount_col)
    st.dataframe(donation_type_counts.style.format({amount_col: "{:,.2f} " + currency}))

    # --- Donation Type Breakdown by Project ---
    st.header("📊 Donation Type Breakdown by Project")

    donation_type_by_project = df.pivot_table(values=amount_col, index='Project', columns='Donation Type',
                                              aggfunc='sum', fill_value=0)

    donation_type_by_project.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='tab20')
    plt.title("Donation Type Breakdown by Project")
    plt.xlabel("Project")
    plt.ylabel(f"Total Donations ({currency})")
    plt.xticks(rotation=45)
    st.pyplot(plt.gcf())
    plt.clf()

    donation_type_by_project = donation_type_by_project
    st.dataframe(donation_type_by_project.style.format({amount_col: "{:,.2f} " + currency}))




    # -------------------------------------------------------------------- Geographic Insights -------------------------------------------------------------

    # --- Top Donor Locations by Count ---
    st.header("📍 Top Donor Locations")

    top_locations = df['Location'].value_counts().nlargest(5)

    sns.barplot(x=top_locations.values, y=top_locations.index, palette='viridis')
    plt.title("Top 5 Locations by Donor Count")
    plt.xlabel("Number of Donors")
    plt.ylabel("Location")
    st.pyplot(plt.gcf())
    plt.clf()

    top_locations = top_locations.to_frame(name=amount_col)
    st.dataframe(top_locations.style.format({amount_col: "{:,.2f} " + currency}))

    # --- Donations by Region ---
    st.header("💰 Donations by Region")

    donations_by_region = df.groupby('Location')[amount_col].sum().sort_values(ascending=False).head(5)

    sns.barplot(x=donations_by_region.values, y=donations_by_region.index, palette='coolwarm')
    plt.title(f"Total Donations by Region ({currency})")
    plt.xlabel(f"Total Donations ({currency})")
    plt.ylabel("Location")
    st.pyplot(plt.gcf())
    plt.clf()

    donations_by_region = donations_by_region.to_frame(name=amount_col)
    st.dataframe(donations_by_region.style.format({amount_col: "{:,.2f} " + currency}))




    # -------------------------------------------------------------------- Project & Campaign Insights -------------------------------------------------------------

    # --- Monthly Donation Trends ---
    st.header("📅 Monthly Donation Trends")

    monthly = df.groupby('Month')[amount_col].sum().reset_index()

    sns.lineplot(data=monthly, x='Month', y=amount_col, marker='o', color='b')
    plt.title("Monthly Donation Totals")
    plt.xlabel("Month")
    plt.ylabel(f"Donation Amount ({currency})")
    plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    st.pyplot(plt.gcf())
    plt.clf()

    st.dataframe(monthly.style.format({amount_col: "{:,.2f} " + currency}))

    # --- Donation Patterns by Day of Week ---
    st.header("📆 Donation Patterns by Day of Week")

    df['DayOfWeek'] = pd.to_datetime(df['Date']).dt.day_name()
    dow = df.groupby('DayOfWeek')[amount_col].sum().sort_values(ascending=False)

    sns.barplot(x=dow.index, y=dow.values, palette='Blues')
    plt.title("Total Donations by Day of Week")
    plt.xlabel("Day of the Week")
    plt.ylabel(f"Donation Amount ({currency})")
    plt.xticks(rotation=45)
    st.pyplot(plt.gcf())
    plt.clf()

    dow = dow.to_frame(name=amount_col)
    st.dataframe(dow.style.format({amount_col: "{:,.2f} " + currency}))

    # --- Donation Amounts Over Time (Yearly Trends) ---
    # st.header("📈 Yearly Donation Trends")
    #
    # df['Year'] = df['Date'].dt.year
    # yearly_donations = df.groupby('Year')[amount_col].sum()
    #
    # sns.lineplot(data=yearly_donations.reset_index(), x='Year', y=amount_col, marker='o', color='g')
    # plt.title("Yearly Donation Trends")
    # plt.xlabel("Year")
    # plt.ylabel(f"Donation Amount ({currency})")
    # st.pyplot(plt.gcf())
    # plt.clf()
    #
    # st.dataframe(yearly_donations.style.format({amount_col: "{:,.2f} " + currency}))

    # --- Seasonal Trends: Donations Around Holidays ---
    st.header("🎉 Seasonal Donation Trends")

    if currency == "BDT":
        holidays = ['2024-12-24', '2024-12-25', '2024-05-23', '2024-05-24']
    else:
        holidays = ['2024-12-24', '2024-12-25', '2024-05-23', '2024-05-24']

    df['Holiday'] = df['Date'].dt.strftime('%Y-%m-%d').isin(holidays)

    holiday_donations = df.groupby('Holiday')[amount_col].sum()

    sns.barplot(x=holiday_donations.index, y=holiday_donations.values, palette='Oranges')
    plt.title("Donation Amounts During Holidays")
    plt.xlabel("Holiday Dates")
    plt.ylabel(f"Donation Amount ({currency})")
    st.pyplot(plt.gcf())
    plt.clf()

    holiday_donations = holiday_donations.to_frame(name=amount_col)
    st.dataframe(holiday_donations.style.format({amount_col: "{:,.2f} " + currency}))

    st.markdown("---")
    st.markdown("📣 **Built with ❤️ for donor engagement & strategic planning.**")

else:
    st.info("Upload a donations CSV to begin.")
