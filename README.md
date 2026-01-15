# 🎯 Daily Task Spinner

A beautiful, feature-rich daily task spinner built with Streamlit that helps you choose and track your daily tasks automatically!

## ✨ Features

- 🎰 **Interactive Spinner Wheel** - Randomly select tasks with a beautiful animated wheel
- 📊 **Automatic Tracking** - Every spin is automatically recorded with timestamps
- 📈 **Rich Analytics** - View task frequency, category distribution, timelines, and completion rates
- 📋 **Comprehensive Reports** - Generate daily, weekly, monthly, and custom reports
- 💾 **Persistent Storage** - All data stored in SQLite database
- ☁️ **Cloud Ready** - Deploy to Streamlit Cloud for free hosting

## 🚀 Quick Start

### Local Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## 🌐 Deploy to Streamlit Cloud (Free Hosting)

1. **Create a GitHub Repository**
   - Go to [GitHub](https://github.com) and create a new repository
   - Push this code to your repository

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy"!

3. **Access Your App**
   - Your app will be live at: `https://[your-app-name].streamlit.app`
   - Data persists across sessions automatically!

## 📖 How to Use

### 1. Spinner Page
- Click "SPIN THE WHEEL" to randomly select a task
- Higher priority tasks have more weight in selection
- Mark tasks as complete or skip to spin again

### 2. Analytics Dashboard
- View real-time statistics and visualizations
- Track task frequency and category distribution
- Monitor completion rates and activity patterns
- See activity heatmaps

### 3. Reports
- Generate daily, weekly, and monthly reports
- Create custom date range reports
- Export reports as text files or CSV

### 4. Manage Tasks
- Add new tasks with categories and priorities
- Edit existing tasks
- Activate/deactivate tasks
- Delete tasks

### 5. History
- View all past spins
- Filter by status or category
- Mark incomplete tasks as complete

## 🎨 Default Tasks

The app comes with these default tasks:
- Gate (Study) - Priority 5
- Job Apply (Career) - Priority 4
- AI Agents (Projects) - Priority 5
- AI Research (Learning) - Priority 4
- C++ (Programming) - Priority 3
- Kaggle (Data Science) - Priority 3
- Backlogs (Admin) - Priority 2
- DSA Patterns (Programming) - Priority 4

Feel free to customize these in the "Manage Tasks" section!

## 🔧 Technology Stack

- **Framework**: Streamlit
- **Visualizations**: Plotly
- **Data Processing**: Pandas
- **Database**: SQLite3

## 📊 Data Storage

All data is stored in `task_spinner.db` (SQLite database):
- Tasks table: Stores all your tasks
- Spin history table: Records every spin with timestamps

**Note**: The `.db` file is gitignored by default. On Streamlit Cloud, the database persists within the app's storage.

## 🎯 Tips for Best Results

1. **Spin Daily** - Build consistency by spinning at least once per day
2. **Mark Completions** - Keep your completion rate accurate
3. **Set Priorities** - Higher priority tasks appear more frequently
4. **Review Analytics** - Check your patterns weekly
5. **Generate Reports** - Use monthly reports to track long-term progress

## 🤝 Contributing

Feel free to customize this app for your needs! Some ideas:
- Add time tracking for tasks
- Integrate with calendar APIs
- Add notifications/reminders
- Create custom themes
- Add task templates

## 📝 License

Free to use and modify as you wish!

## 🆘 Troubleshooting

**App won't start locally?**
- Make sure Python 3.8+ is installed
- Run `pip install -r requirements.txt` again

**Data not persisting on Streamlit Cloud?**
- This is normal - Streamlit Cloud provides persistent storage automatically
- Don't commit the .db file to git

**Spinner not showing tasks?**
- Go to "Manage Tasks" and ensure you have active tasks

## 📧 Support

For issues or questions, create an issue in the GitHub repository.

---

**Made with ❤️ using Streamlit**

Enjoy your productive journey! 🚀
