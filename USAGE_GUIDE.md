# How to Use the AI Task Manager

## Step-by-Step Workflow

### 1. Extract Tasks (AI Extraction Tab)
- Paste your meeting notes or text into the text area
- Click "🔍 Extract Action Items" 
- The AI will analyze and extract tasks with priorities, categories, and due dates
- Review and edit the extracted items if needed

### 2. Add Tasks to System
- After extracting items, you'll see a "✅ Add All Tasks" button
- When clicked, this should show:
  - "Processing X items..." message
  - Step-by-step progress: "Adding task 1: [Task Name]"
  - "✅ Task saved with ID: [Number]" for each task
  - Success message with balloons animation
  - Automatic refresh of the page

### 3. View Your Tasks
- Go to "📋 Task Management" tab to see all your tasks
- Go to "📊 Analytics" tab to see charts and visualizations
- Go to "💾 Data Management" tab to export or manage data

## Troubleshooting

### If "Add All Tasks" doesn't work:
1. Check the Data Management tab for current task counts
2. Look for error messages in the console
3. Try the "🔄 Reload Data from Database" button
4. Check if you have any extracted items to add

### If visualizations are empty:
- Make sure you have tasks in your system first
- Check the Data Management tab to see task counts
- Use "🔄 Reload Data from Database" if needed

## Expected Behavior
- Tasks should persist between sessions
- Charts update automatically when tasks are added
- Export buttons create downloadable CSV files
- All data is stored in SQLite database