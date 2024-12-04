using System;
using System.Diagnostics;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.IO;
using System.Text;
using System.Net.Http;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System.Linq;
using System.Net;
using System.Net.NetworkInformation;
using System.Management;
using System.Collections;
using Shell32;
using System.Collections.Generic;
using System.ComponentModel;
//using System.Windows.Forms;

namespace Surveillance
{
    public class Rootobject
    {
        public Parsedresult[] ParsedResults { get; set; }
        public int OCRExitCode { get; set; }
        public bool IsErroredOnProcessing { get; set; }
        public string ErrorMessage { get; set; }
        public string ErrorDetails { get; set; }
    }

    public class Parsedresult
    {
        public object FileParseExitCode { get; set; }
        public string ParsedText { get; set; }
        public string ErrorMessage { get; set; }
        public string ErrorDetails { get; set; }
    }
    class Program
    {
        //public static AllInputSources lastInput;
        /////////////////////////////////// ALL PARAMETERS ///////////////////////////////////////////////
        // Input parameters (Mouse Click, Keystroke)
        public static KeyboardInput keyboard;
        public static MouseInput mouse;

        // timer and amount of time to delay
        public static Timer timer_wait = new Timer();
        public static Timer timer_send_data = new Timer();
        public static Timer timer_resume_reminder = new Timer();
        public static int timeWait;
        public static int timeWait_ToSendData;
        public static int timeWait_ResumeReminder;

        // window title, application/process id
        public static String wtitle = "";
        public static String wappName = "";
        public static int wprocId = 0;

        // LOG PERMISSION
        public static bool logPermision = true;

        // For Application Icon Notification
        public static Form1 form1;

        // Time Delay Setting
        public static int TwoSeconds = 2; 
        public static int FiveSeconds = 500000000;
        public static int ThirtySeconds = 30;
        public static int TenMinutes = 600;
        public static bool isIdle = true;
        public static String userID = "";
        public static String lang = "eng+fin";
        public static String queueFolder = "02";
        public static int NumberOfKeyPressed = 0;

        // Arbitrary setting
        // Checking http response
        public static bool wait_http_response;

        // Menu Notify Item
        private static System.Windows.Forms.ContextMenuStrip contextMenu1;
        private static System.Windows.Forms.ToolStripMenuItem menuItem1;
        private static System.Windows.Forms.ToolStripMenuItem menuItem2;
        private static List<ToolStripMenuItem> allAppItems = new List<ToolStripMenuItem>();
        private static List<ToolStripMenuItem> allChromeItems = new List<ToolStripMenuItem>();

        private static AccessInfo[] chromehistory;
        private static AccessInfo[] appNames;

        [STAThread]
        static void Main(string[] args)
        {
            userID = GetMACAddress();
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            timeWait = ThirtySeconds;
            timeWait_ToSendData = FiveSeconds;
            timeWait_ResumeReminder = TenMinutes;

            keyboard = new KeyboardInput();
            keyboard.KeyBoardKeyPressed += userActivity;

            mouse = new MouseInput();
            mouse.MouseWheel += userActivity;
            mouse.MouseLClick += userActivity_KeyPressed;
            mouse.MouseRClick += userActivity_KeyPressed;
            var handle = GetConsoleWindow();

            timer_wait.Interval = 1000;
            timer_wait.Enabled = true;
            DoInBackground(null, null);
            timer_wait.Tick += new EventHandler(DoInBackground);
            timer_wait.Start();

            timer_send_data.Interval = 1000;
            timer_send_data.Enabled = true;
            DoSendData(null, null);
            timer_send_data.Tick += new EventHandler(DoSendData);
            timer_send_data.Start();

            timer_resume_reminder.Interval = 1000;
            timer_resume_reminder.Enabled = true;
            ResumeReminder(null, null);
            timer_resume_reminder.Tick += new EventHandler(ResumeReminder);
            timer_resume_reminder.Stop();

            wait_http_response = false;

            // Hide
            //ShowWindow(handle, SW_HIDE);

            //Application.Run();
            form1 = new Form1();
            form1.notifyIcon1.MouseDown += EnableDisableLog;
            // Menu Notify Item
            contextMenu1 = new System.Windows.Forms.ContextMenuStrip();
            menuItem1 = new System.Windows.Forms.ToolStripMenuItem();
            menuItem2 = new System.Windows.Forms.ToolStripMenuItem();

            // Initialize contextMenu1
            contextMenu1.Items.AddRange(
                        new System.Windows.Forms.ToolStripItem[] { menuItem2, menuItem1 });

            // Initialize menuItem1
            //menuItem1.Index = 0;
            menuItem1.Text = "E&xit";
            menuItem1.Click += new System.EventHandler(menuItem1_Click);
            // Initialize menuItem2
            //menuItem2.Index = 0;
            menuItem2.Text = "Apps not to track";
            menuItem2.DropDown.Closing += contextMenuStrip_Closing;

            // App name to add
            AccessInfo[] appNames = new MyUtil().getAppsFromFile();
            BackgroundWorker appFilterWorker = new BackgroundWorker();
            appFilterWorker.WorkerReportsProgress = true;
            appFilterWorker.DoWork += new DoWorkEventHandler(backgroundWorker_AppFilter);
            appFilterWorker.RunWorkerCompleted += new RunWorkerCompletedEventHandler(backgroundWorker_AppFilterCompleted);
            if (appFilterWorker.IsBusy != true)
                appFilterWorker.RunWorkerAsync();

            form1.notifyIcon1.ContextMenuStrip = contextMenu1;
            Application.Run(form1);

        }

        private static void backgroundWorker_AppFilter(object sender, DoWorkEventArgs e)
        {
            appNames = new MyUtil().getAppsFromFile();
            chromehistory = new MyUtil().getChromeHistoryFromFile();
        }
        private static void backgroundWorker_AppFilterCompleted(object sender, RunWorkerCompletedEventArgs e)
        {
            Array.ForEach(appNames, x => addApps(x));
            Debug.WriteLine("Done!!!!");
        }

        private static void contextMenuStrip_Closing(object sender, ToolStripDropDownClosingEventArgs e)
        {
            if (e.CloseReason == ToolStripDropDownCloseReason.ItemClicked)
                e.Cancel = true;
            else
            {
                new System.Threading.Thread(delegate ()
                {
                    Debug.WriteLine("Saving filter file");
                    List<AccessInfo> appList = new List<AccessInfo>();
                    foreach (ToolStripMenuItem item in allAppItems)
                    {
                        String filtered = "0";
                        if (item.Checked)
                            filtered = "1";
                        AccessInfo app = new AccessInfo()
                        {
                            Name = item.Text,
                            IsFiltered = filtered
                        };
                        appList.Add(app);
                    }

                    // Write extra info to files
                    String path = @"source/appACL.txt";
                    new MyUtil().WriteToFile(path, JsonConvert.SerializeObject(appList.ToArray()).ToString());
                }).Start();
            }
        }

        private static void chromeMenu_Closing(object sender, ToolStripDropDownClosingEventArgs e)
        {
            if (e.CloseReason == ToolStripDropDownCloseReason.ItemClicked)
                e.Cancel = true;
            else
            {
                new System.Threading.Thread(delegate ()
                {
                    Debug.WriteLine("chrome saving filter list");
                    List<AccessInfo> chromeList = new List<AccessInfo>();
                    foreach (ToolStripMenuItem item in allChromeItems)
                    {
                        String filtered = "0";
                        if (item.Checked)
                            filtered = "1";
                        AccessInfo app = new AccessInfo()
                        {
                            Name = item.Text,
                            IsFiltered = filtered
                        };
                        chromeList.Add(app);
                    }

                    // Write extra info to files
                    String path = @"source/chromeACL.txt";
                    new MyUtil().WriteToFile(path, JsonConvert.SerializeObject(chromeList.ToArray()).ToString());

                }).Start();
            }
        }

        private static void addApps(AccessInfo app)
        {
            ToolStripMenuItem app1 = new ToolStripMenuItem(app.Name);
            allAppItems.Add(app1);
            if (app.Name.ToLower().Contains("chrome"))
            {
                foreach (AccessInfo h in chromehistory)
                {
                    ToolStripMenuItem app2 = new ToolStripMenuItem(h.Name);
                    if (h.IsFiltered.Equals("1"))
                        app2.Checked = true;
                    else
                        app2.Checked = false;
                    app2.Click += new System.EventHandler(appItem_Click);
                    allChromeItems.Add(app2);
                    app1.DropDownItems.Add(app2);
                }
                app1.DropDown.Closing += chromeMenu_Closing;
            }
            else
            {
                if (app.IsFiltered.Equals("1"))
                    app1.Checked = true;
                else
                    app1.Checked = false;
                app1.Click += new System.EventHandler(appItem_Click);
            }
            menuItem2.DropDownItems.Add(app1);
        }

        private static void appItem_Click(object sender, EventArgs e)
        {
            if (((ToolStripMenuItem)sender).Checked)
                ((ToolStripMenuItem)sender).Checked = false;
            else
                ((ToolStripMenuItem)sender).Checked = true;

            //form1.Show();
        }
        
        // Exit Program upon clicking on "Exit" button in Context Menu
        static void menuItem1_Click(object Sender, EventArgs e)
        {
            // Close the form, which closes the application.
            Application.Exit();
        }


        // Enable and Disable function of The logger
        static void EnableDisableLog(object sender, EventArgs e)
        {
           
            //Debug.WriteLine("Enable/Disable Log");
            System.Windows.Forms.NotifyIcon icon = (System.Windows.Forms.NotifyIcon)sender;
            logPermision = logPermision ? false : true;
            // Turn on logging event
            if (logPermision)
            {
                icon.Icon = Properties.Resources.Record_Ico_;
                icon.Text = "Activities are logging. ID:"+userID;
                ResetCountdown();
            }
            // Turn off logging event
            else
            {
                icon.Text = "Logging is stopped, please resume. ID:" + userID;
                icon.Icon = Properties.Resources.Pause_Ico_;
                StopCountDown();
            }
        }

        static ArrayList readAllFilePaths()
        {
            ArrayList output = new ArrayList();
            try
            {
                if (!File.ReadAllText(@"source/AllFilePaths.txt").Trim().Equals(""))
                {
                    string[] filepaths = File.ReadAllText(@"source/AllFilePaths.txt").Split(';');
                    foreach (string path in filepaths)
                    {
                        output.Add(path);
                    }
                }
            }
            catch(Exception exception)
            {
                WriteToFile("source/logs.txt", DateTime.Now.ToString() + " : " + exception.ToString());
            }

            return output;
        }

        static void appendNewFilePath()
        {
            try
            {
                ArrayList paths = readAllFilePaths();
                ArrayList old_paths = readAllFilePaths();
                string filename;
                foreach (SHDocVw.InternetExplorer window in new SHDocVw.ShellWindows())
                {
                    filename = Path.GetFileNameWithoutExtension(window.FullName).ToLower();
                    if (filename.ToLowerInvariant() == "explorer")
                    {
                        FolderItems items = ((IShellFolderViewDual2)window.Document).SelectedItems();
                        foreach (FolderItem item in items)
                        {
                            if (!paths.Contains(item.Path))
                            {
                                paths.Add(item.Path);
                            }
                            //selected.Add(item.Path);
                        }
                    }
                }
                if (old_paths.Count < paths.Count)
                {
                    //Debug.WriteLine("NEW PATHS FOUND!!!!!!!!!!!!!!!!!!!!!!!!!");
                    using (StreamWriter sw = new StreamWriter("source/AllFilePaths.txt", false))
                    {
                        sw.Write(string.Join(";", (string[])paths.ToArray(Type.GetType("System.String"))));
                        sw.Close();
                    }
                }
            }
            catch(Exception exception)
            {
                WriteToFile("source/logs.txt", DateTime.Now.ToString() + " : " + exception.ToString());
            }
        }

        // Mouse Input Event
        static void userActivity(object sender, EventArgs e)
        {
            //appendNewFilePath();
            //if (logPermision && isIdle)
            if (logPermision && NumberOfKeyPressed < 100)
            {
                NumberOfKeyPressed++;
                Debug.WriteLine("Active!");
                Debug.WriteLine("Key Pressed ! " + NumberOfKeyPressed.ToString());
                isIdle = false;
                timeWait = TwoSeconds;
            }
        }
        
        static void userActivity_KeyPressed(object sender, EventArgs e)
        {
            new System.Threading.Thread(delegate ()
            {
                appendNewFilePath();
            }).Start();
            if (logPermision && NumberOfKeyPressed<100)
            {
                NumberOfKeyPressed++;
                Debug.WriteLine("Active!");
                Debug.WriteLine("Key Pressed ! "+ NumberOfKeyPressed.ToString());
                isIdle = false;
                timeWait = TwoSeconds;
            }
        }

        // Do Screen Capture in background thread
        static void DoInBackground(object sender, EventArgs e)
        {
            if (timeWait == 0)
            {
                new System.Threading.Thread(delegate ()
                {
                    //Debug.WriteLine(userInput.ToString());
                    Debug.WriteLine("Start screen capture");
                    TakeScreenShot();
                    Debug.WriteLine("Idle!");
                    isIdle = true;
                    timeWait = ThirtySeconds;

                }).Start();
                //timer_wait.Stop();
            }
            else
            {
                Debug.WriteLine("action: "+timeWait.ToString());
                if (timeWait > 0)
                    timeWait--;
            }
        }
        // Reminder function to remind the user to resume the logger if the logger is turn off.
        public static void ResumeReminder(object sender, EventArgs e)
        {
            if (timeWait_ResumeReminder == 0)
            {
                form1.notifyIcon1.ShowBalloonTip(500, "INFO", "Please remember to RESUME ME after your private activities are done", ToolTipIcon.Info);
                timeWait_ResumeReminder = TenMinutes;
                timer_resume_reminder.Start();
            }
            else
            {
                if (timeWait_ResumeReminder > 0)
                    timeWait_ResumeReminder--;
            }

        }

        // Periodically send offline data (screenshot & activity logs) to the backend (The plan is 30-second interval)
        public static void DoSendData(object sender, EventArgs e)
        {
            if (timeWait_ToSendData == 0)
            {
                timeWait_ToSendData--;
                try
                {
                    new System.Threading.Thread(delegate()
                    {
                        //Send Data to Server
                        String[] files = Directory.GetFiles(@"source/temp/", "*", SearchOption.TopDirectoryOnly);
                        for (int i = 0; i < files.Length && i < 10; i++)
                        {
                            while (wait_http_response)
                            {
                                System.Threading.Thread.Sleep(500);
                                //Debug.WriteLine("wait....");
                            }
                            String eachLog = (Path.GetFileName(files[i])).Replace(".jpeg", "");
                            String extraLogToBeSent = File.Exists(@"source/extras/" + eachLog + ".txt") ? File.ReadAllText(@"source/extras/" + eachLog + ".txt") : "<empty>";
                            DoRequestServer(eachLog, extraLogToBeSent);
                        }
                        //Reset to loop
                        timeWait_ToSendData = FiveSeconds;
                    }).Start();
                }
                catch (Exception exception)
                {
                    //Debug.WriteLine(exception.ToString());
                    WriteToFile("source/logs.txt", DateTime.Now.ToString() + " : " + exception.ToString());
                }
            }
            else
            {
                //Debug.WriteLine(timeWait_ToSendData.ToString());
                if (timeWait_ToSendData > 0)
                    timeWait_ToSendData--;
            }
        }

        // Un-use: Validate the existence of license id in LicenseID.txt
        /*public static bool IsLicenseIDValid()
        {
            //String LicenseID = File.Exists(@"source/LicenseID.txt") ? System.Text.RegularExpressions.Regex.Replace(File.ReadAllText(@"source/LicenseID.txt").Trim(), @"\t|\n|\r", "") : "<empty>";
            String LicenseID = userID;
            //Debug.WriteLine(LicenseID);
            if (LicenseID.Equals("<empty>") || LicenseID.Equals(""))
            {
                form1.notifyIcon1.Visible = true;
                form1.notifyIcon1.ShowBalloonTip(500, "Warning", "License file is Missing or Empty, Please contact us for support", ToolTipIcon.Warning);
                return false;
            }
            else
            {
                // Check key from server
                bool found = false;
                try
                {
                    string url_req = "https://reknowdesktopsurveillance.hiit.fi/checklicenseid.php?licenseid=" + LicenseID;
                    //Debug.WriteLine(url_req);
                    using (var client = new WebClient())
                    {
                        JObject result = JObject.Parse(client.DownloadString(url_req));
                        //Debug.WriteLine(result["hits"]["total"]);
                        if (result["hits"]["total"].ToString().Equals("1"))
                        {
                            found = true;
                        }
                        else
                        {
                            form1.notifyIcon1.Visible = true;
                            form1.notifyIcon1.ShowBalloonTip(500, "Warning", "License ID is Invalid, Please contact us for support", ToolTipIcon.Warning);
                        }
                    }
                }
                catch (WebException e)
                {
                    form1.notifyIcon1.Visible = true;
                    form1.notifyIcon1.ShowBalloonTip(500, "Warning", "Could not reach our server", ToolTipIcon.Warning);
                    //Debug.WriteLine(e.ToString());
                    WriteToFile("source/logs.txt", DateTime.Now.ToString()+" : "+e.ToString());
                }
                return found;
            }
        }*/

        // CAPTURE SCREENSHOTs & RECORD COMPUTER LOGS (saved offline on local computer)
        public static void TakeScreenShot()
        {
            try
            {
                //String url = ScreenCapture.GetURL();
                String appName = ScreenCapture.GetAppName();
                String url = ScreenCapture.GetURL();
                String windowTitle = ScreenCapture.GetWindowTitle();
                Debug.WriteLine("TITLE:::::::::::::::::::"+windowTitle);
                if (windowTitle.Contains("ProIR")){
                    return;
                }
                String fileName = (DateTime.UtcNow.Subtract(new DateTime(1970, 1, 1))).TotalSeconds.ToString();
                fileName = isIdle ? fileName + "_idle" : fileName;
                //Debug.WriteLine("fileName : " + fileName);
                //Debug.WriteLine("url: " + url);
                //Debug.WriteLine("app: " + appName);
                //Debug.WriteLine("title: " + windowTitle);
                var image = ScreenCapture.CaptureActiveWindow();
                // Write to JSON
                JObject computerLog = new JObject();
                computerLog["url"] = url;
                computerLog["appname"] = appName;
                computerLog["title"] = windowTitle;
                computerLog["filename"] = fileName;

                // Write extra info to files
                // url
                String path = @"source/extras/" + fileName + ".txt";
                WriteToFile(path, computerLog.ToString());
                // screenshot
                path = @"source/temp/" + fileName + ".jpeg";
                //image.Save(@"temp/" + fileName + ".png", System.Drawing.Imaging.ImageFormat.Png);
                image.Save(path, System.Drawing.Imaging.ImageFormat.Jpeg);
                NumberOfKeyPressed = 0;
            }
            catch (Exception e)
            {
                //Console.WriteLine(e.ToString());
                WriteToFile("source/logs.txt", DateTime.Now.ToString()+" : "+e.ToString());
            }
        }

        // Write string to file function
        private static void WriteToFile(string path, string text)
        {
            using (StreamWriter sw = new StreamWriter(path, true))
            {
                sw.WriteLine(text);
                sw.Close();
            }
        }
        private static void TimerCallback(Object o)
        {
            // Display the date/time when this method got called.
            Console.WriteLine("In TimerCallback: " + DateTime.Now);
            // Force a garbage collection to occur for this demo.
            GC.Collect();
        }
        // Reset / Resume count-down timers and Turn Off timer of resume reminder function
        static void ResetCountdown()
        {
            timeWait = ThirtySeconds;
            isIdle = true;
            //timeWait_ToSendData = FiveSeconds;
            //timer_wait.Stop();
            timer_wait.Start();
            //timer_send_data.Stop();
            timer_send_data.Start();
            // Turn off resume reminder when the logger is running
            timer_resume_reminder.Stop();
        }
        // Pause all count down timers and Turn On timer of resume reminder function
        static void StopCountDown()
        {
            timeWait = ThirtySeconds;
            isIdle = true;
            timer_wait.Stop();
            timeWait_ToSendData = FiveSeconds;
            timer_send_data.Stop();
            // Turn on Resume Reminder when logger is stopped
            //timer_resume_reminder.Stop();
            timeWait_ResumeReminder = TenMinutes;
            timer_resume_reminder.Start();
        }

        // UPLOAD ALL SCREENSHOTS AND COMPUTER LOGS FROM LOCAL COMPUTER TO THE BACKEND (every 30 seconds)
        //public static async void DoRequestServer(String fileName, String windowTitle, String url, String appName, String location)
        public static async void DoRequestServer(String fileName, String extraLog)
        {
            wait_http_response = true;
            String ImagePath = (@"source/temp/" + fileName + ".jpeg");
            String TextPath = (@"source/logs/" + fileName + ".txt");
            String SettingFile = @"source/settings.txt";
            try
            {
                JObject Settings = JObject.Parse(File.ReadAllText(SettingFile));
                String LicenseID = userID;
                JObject extraLogToBeSent = JObject.Parse(extraLog);
                extraLogToBeSent["licenseid"] = LicenseID;
                if (string.IsNullOrEmpty(ImagePath))
                    return;
            
                HttpClient httpClient = new HttpClient();
                httpClient.Timeout = new TimeSpan(1, 1, 1);


                MultipartFormDataContent form = new MultipartFormDataContent();
                //form.Add(new StringContent("d5aef703ba88957"), "apikey"); //Added api key in form data
                form.Add(new StringContent(extraLogToBeSent.ToString()), "extra");
                //form.Add(new StringContent(GetUniqueID()), "username");
                form.Add(new StringContent(LicenseID), "username");
                form.Add(new StringContent(Settings["lang"].ToString()), "lang");
                form.Add(new StringContent(Settings["queuefolder"].ToString()), "queuefolder");
                if (string.IsNullOrEmpty(ImagePath) == false)
                {
                    byte[] imageData = File.ReadAllBytes(ImagePath);
                    form.Add(new ByteArrayContent(imageData, 0, imageData.Length), "image", fileName+".jpeg");
                }
                
                HttpResponseMessage response = await httpClient.PostAsync("https://reknowdesktopsurveillance.hiit.fi/"+ Settings["backend"].ToString(), form);

                string strContent = await response.Content.ReadAsStringAsync();
                
                // Delete data after upload
                //Debug.WriteLine(strContent);
                if (strContent.Equals("file uploaded"))
                {
                    System.IO.File.Delete(ImagePath);
                    System.IO.File.Delete(@"source/extras/" + fileName + ".txt");
                }
                wait_http_response = false;
            }
            catch (Exception e)
            {
                //MessageBox.Show("Ooops");
                wait_http_response = false;
                WriteToFile("source/logs.txt", DateTime.Now.ToString()+" : "+e.ToString());
            }
        }

        public static string GetMACAddress()
        {
            NetworkInterface[] nics = NetworkInterface.GetAllNetworkInterfaces();
            String sMacAddress = string.Empty;
            foreach (NetworkInterface adapter in nics)
            {
                if (sMacAddress == String.Empty)// only return MAC Address from first card  
                {
                    //IPInterfaceProperties properties = adapter.GetIPProperties(); Line is not required
                    sMacAddress = adapter.GetPhysicalAddress().ToString();
                }
            }
            return sMacAddress;
        }
        public static string QuoteArgument(string arg)
        {
            // The inverse of http://msdn.microsoft.com/en-us/library/system.environment.getcommandlineargs.aspx

            // Suppose we wish to get after unquoting: \\share\"some folder"\
            // We should provide: "\\share\\\"some folder\"\\"

            // Escape quotes ==> \\share\\\"some folder\"\
            // For quotes with N preceding backslashes, replace with 2k+1 preceding backslashes.
            var res = new StringBuilder();
            // For sequences of backslashes before quotes:
            // odd ==> 2x+1, even => 2x ==> "\\share\\\"some folder"
            var numBackslashes = 0;
            for (var i = 0; i < arg.Length; ++i)
            {
                if (arg[i] == '"')
                {
                    res.Append('\\', 2 * numBackslashes + 1);
                    res.Append('"');
                    numBackslashes = 0;
                }
                else if (arg[i] == '\\')
                {
                    numBackslashes++;
                }
                else
                {
                    res.Append('\\', numBackslashes);
                    res.Append(arg[i]);
                    numBackslashes = 0;
                }
            }
            res.Append('\\', numBackslashes);

            // Enquote, doubling last sequence of backslashes ==> "\\share\\\"some folder\"\\"
            var numTrailingBackslashes = 0;
            for (var i = res.Length - 1; i > 0; --i)
            {
                if (res[i] != '\\')
                {
                    numTrailingBackslashes = res.Length - 1 - i;
                    break;
                }
            }
            res.Append('\\', numTrailingBackslashes);

            return '"' + res.ToString() + '"';
        }
        [DllImport("kernel32.dll")]
        static extern IntPtr GetConsoleWindow();

        [DllImport("user32.dll")]
        static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        const int SW_HIDE = 0;
    }
}
