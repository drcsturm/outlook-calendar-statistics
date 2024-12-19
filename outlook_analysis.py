import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def manipulate_raw_data(uploaded_file, custom_subjects_to_remove):
    df_raw = pd.read_csv(uploaded_file)

    # Combine default subjects with custom subjects to remove
    default_subjects = [
    ]

    # Add custom subjects to remove
    if custom_subjects_to_remove:
        subjects_to_remove = default_subjects + [s.strip() for s in custom_subjects_to_remove.split(',')]
    else:
        subjects_to_remove = default_subjects

    df_raw['StartTime'] = pd.to_datetime(df_raw['Start Date'] + ' ' + df_raw['Start Time'], format='%m/%d/%Y %I:%M:%S %p')
    df_raw['EndTime'] = pd.to_datetime(df_raw['End Date'] + ' ' + df_raw['End Time'], format='%m/%d/%Y %I:%M:%S %p')

    df_raw = df_raw[(df_raw['StartTime'] >= '2024-01-01') & (df_raw['StartTime'] <= '2024-12-31')]
    df_raw = df_raw[~(df_raw.Subject.isin(subjects_to_remove))]
    df_raw = df_raw[~(pd.isna(df_raw.Subject))]
    df_raw = df_raw[df_raw['Show time as'] == 2]
    df_raw = df_raw.sort_values('StartTime')
    df_raw['start_month'] = df_raw['StartTime'].dt.month
    df_raw['start_day'] = df_raw['StartTime'].dt.day
    df_raw['Duration'] = df_raw['EndTime'] - df_raw['StartTime']

    return df_raw


def group_data(df_raw):
    # Your existing group_data function remains the same
    groups = df_raw.groupby('start_month')
    days_per_month = groups.start_day.nunique()
    meeting_count = groups.Subject.count()
    total_meeting_time = groups.Duration.sum().dt.total_seconds()/3600
    df = pd.concat([days_per_month, meeting_count, total_meeting_time], axis=1)
    df.columns = ['Days / Month', 'Meeting Count', 'Total Time (hr)']
    df['Meetings / Day'] = round(meeting_count / days_per_month, 1)
    df['Avg Meeting Length (Min)'] = (df['Total Time (hr)']*60 / df['Meeting Count']).astype(int)
    # Convert month numbers to names
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    df['Month'] = df.index.map(month_names)
    df = df[['Month', 'Days / Month', 'Meeting Count', 'Total Time (hr)', 'Meetings / Day', 'Avg Meeting Length (Min)']]
    return df


def create_graphs(df):
    df_reversed = df.iloc[::-1]
    
    # Create all your plots and return them in a dictionary
    plots = {}
    
    # Stacked Area Chart
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df['Month'], y=df['Meeting Count'],
                             mode='lines', fill='tonexty', name='Meeting Count'))
    fig2.add_trace(go.Scatter(x=df['Month'], y=df['Avg Meeting Length (Min)'],
                             mode='lines', fill='tonexty', name='Avg Duration',
                             marker=dict(color='green')))
    fig2.update_layout(title='Meeting Metrics Area Chart', xaxis_tickangle=-45)
    plots['area_chart'] = fig2

    # Add all other plots similarly...
    # (Adding just a couple more as examples, you can add the rest similarly)

    # Polar Bar Chart
    fig3 = go.Figure(go.Barpolar(
        r=df_reversed['Meeting Count'],
        theta=df_reversed['Month'],
        width=1
    ))
    fig3.update_layout(
        title='Meeting Count Polar Distribution',
        polar=dict(
            angularaxis=dict(
                direction='counterclockwise',
                rotation=90
            )
        )
    )
    plots['polar_bar'] = fig3

    # 3D Scatter Plot
    fig4 = go.Figure(data=[go.Scatter3d(
        x=df['Meeting Count'],
        y=df['Meetings / Day'],
        z=df['Avg Meeting Length (Min)'],
        mode='markers+text',
        text=df['Month'],
        marker=dict(
            size=10,
            color=df.index,
            colorscale='Viridis',
        )
    )])
    fig4.update_layout(title='3D Meeting Metrics Visualization',
                       height=800,
                       scene=dict(
                            xaxis_title='Meeting Count',
                            yaxis_title='Meetings / Day',
                            zaxis_title='Avg Meeting Length (Min)'
                        )
                    )
    plots['scatter_3d'] = fig4

    # 4. Radial Bar Chart
    fig5 = go.Figure()
    fig5.add_trace(go.Scatterpolar(
        r=df_reversed['Meeting Count'],
        theta=df_reversed['Month'],
        fill='toself',
        name='Meeting Count'
    ))
    fig5.add_trace(go.Scatterpolar(
        r=df_reversed['Avg Meeting Length (Min)'],
        theta=df_reversed['Month'],
        fill='toself',
        name='Avg Duration',
        marker=dict(color='green')
    ))
    fig5.update_layout(title='Radial Meeting Metrics',
        polar=dict(
            angularaxis=dict(
                direction='counterclockwise',  # Set direction
                rotation=90  # Rotate 90 degrees (starts from the top)
            )
        )
                    )
    plots['radial_bar_chart'] = fig5

    # 9. Spider Plot with Multiple Metrics
    fig6 = go.Figure()
    metrics = ['Meeting Count', 'Meetings / Day', 'Avg Meeting Length (Min)']
    # Normalize the data for better visualization
    normalized_data = df[metrics].apply(lambda x: (x - x.min()) / (x.max() - x.min()))

    for month in df['Month']:
        fig6.add_trace(go.Scatterpolar(
            r=normalized_data.loc[df['Month'] == month].iloc[0],
            theta=metrics,
            fill='toself',
            name=month
        ))
    fig6.update_layout(title="Normalized Meeting Metrics by Month")
    plots['spider_plot_with_metrics'] = fig6

    # 10. Composite Bar-Line Chart with Moving Averages
    fig7 = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bars for meeting count
    fig7.add_trace(
        go.Bar(x=df['Month'], y=df['Meeting Count'], name="Meeting Count"),
        secondary_y=False,
    )

    # Add line for moving average
    fig7.add_trace(
        go.Scatter(x=df['Month'], 
                y=df['Avg Meeting Length (Min)'].rolling(window=3).mean(),
                name="3-Month Moving Average (Min)",
                line=dict(color='red')),
        secondary_y=True,
    )

    # Add another metric
    fig7.add_trace(
        go.Scatter(x=df['Month'], 
                   y=df['Avg Meeting Length (Min)'],
                   name="Avg Duration",
                   line=dict(color='green')),
        secondary_y=True,
    )

    fig7.update_layout(
        title="Meeting Metrics with Moving Averages",
        xaxis_tickangle=-45,
        barmode='group'
    )
    plots['composite_bar_chart'] = fig7

    return plots


def main():
    st.title('Outlook Calendar Meeting Analysis')

    with st.expander('Instructions to export Outlook calendar as CSV'):
        for i, col in enumerate(st.columns(3)):
            caption = ''
            if i == 0:
                caption = 'Open Outlook and click on File, then "Open & Export"'
            col.image(f'outlook_{i + 1}.PNG', caption=caption)

        for i, col in enumerate(st.columns(3)):
            col.image(f'outlook_{i + 1 + 3}.PNG')

    # File uploader
    uploaded_file = st.file_uploader("Choose your Outlook calendar CSV file", type="csv")

    # Text input for custom subjects to remove
    custom_subjects = st.text_input(
        "Enter meeting subjects to remove from analysis (comma-separated)",
        help="Example: Team Meeting, Daily Standup, Weekly Review"
    )

    if uploaded_file is not None:
        # Process the data
        df_raw = manipulate_raw_data(uploaded_file, custom_subjects)
        df_grouped = group_data(df_raw)

        # Display some basic statistics
        st.subheader("Basic Statistics (only considers meetings set to Busy)")
        st.dataframe(df_grouped, height=458, hide_index=True)
        st.subheader("Unique Meeting Names")
        st.dataframe(df_raw.Subject.value_counts())

        # Create and display plots
        plots = create_graphs(df_grouped)

        # Display each plot in its own section
        for key, plot in plots.items():
            st.plotly_chart(plot, use_container_width=True)


if __name__ == "__main__":
    main()
