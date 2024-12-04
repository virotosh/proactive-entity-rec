using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Runtime.InteropServices;
using System.Drawing;
using System.Drawing.Imaging;
using System.Diagnostics;
using System.Windows.Automation;
using System.Text.RegularExpressions;
using mshtml;
using System.Management;
using System.Collections;
using System.IO;
using Shell32;
using System.Data.SQLite;
using Newtonsoft.Json.Linq;
using NDde.Client;

namespace Surveillance
{
    /// <summary>
    /// Provides functions to capture the entire screen, or a particular window, and save it to a file.
    /// </summary>
    public class ScreenCapture
    {
        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern IntPtr GetWindowRect(IntPtr hWnd, ref Rect rect);

        [DllImport("user32.dll")]
        private static extern IntPtr ClientToScreen(IntPtr hWnd, ref Rect rect);

        [DllImport("user32.dll")]
        private static extern IntPtr GetClientRect(IntPtr hWnd, ref Rect rect);

        [DllImport("user32.dll", SetLastError = true)]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        static extern uint GetModuleFileName(IntPtr hwnd,
           StringBuilder lpszFileName, uint cchFileNameMax);
        public static String title = "";
        public static IntPtr hWnd = GetForegroundWindow();

        [StructLayout(LayoutKind.Sequential)]
        private struct Rect
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        [DllImport("user32.dll", CharSet = CharSet.Auto, ExactSpelling = true)]
        public static extern IntPtr GetDesktopWindow();


        public static Image CaptureDesktop()
        {
            return CaptureWindow(GetDesktopWindow());
        }

        public static bool IsWindowSwitch(int Id)
        {
            //IntPtr hWnd = GetForegroundWindow();
            uint procId = 0;
            GetWindowThreadProcessId(hWnd, out procId);
            var proc = Process.GetProcessById((int)procId);
            //Console.WriteLine(title);
            //Console.WriteLine(GetWindowTitle());
            
            if(Id != (int)procId)
            {
                return true;
            }
            else
            {
                return false;
            }
        }
        public static bool IsApplicationSwitch(String app)
        {
            if (!GetAppName().Equals(app))
            {
                return true;
            }
            else
            {
                return false;
            }
        }

        public static string QueryResult(string query)
        {
            query = query.Replace(" - Mozilla Firefox", "");
            query = query.Replace(" (Private Browsing)", "");
            string result = "";
            string[] filesindirectory = Directory.GetDirectories(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData) + "\\Mozilla\\Firefox\\Profiles\\");
            Debug.WriteLine("LOOK HERE::::::" + filesindirectory[0]);
            String firefoxFolder = filesindirectory[0];
            Debug.WriteLine("HEYYYYY" + firefoxFolder);
            SQLiteConnection sqlite = new SQLiteConnection("Data Source="+ Path.Combine(firefoxFolder,"places.sqlite"));
            
            try
            {
                Debug.WriteLine("HERE");
                sqlite.Open();  //Initiate connection to the db
                SQLiteCommand cmd = sqlite.CreateCommand();
                cmd.CommandText = query;  //set the passed query
                result = cmd.ExecuteScalar().ToString();
                Debug.WriteLine(result);
            }
            catch(Exception exception)
            {
                WriteToFile("source/logs.txt", DateTime.Now.ToString() + " : " + exception.ToString());
                sqlite.Close();
            }
            return result;
        }

        public static bool IsTabSwitch(String title)
        {
            //IntPtr hWnd = GetForegroundWindow();
            uint procId = 0;
            GetWindowThreadProcessId(hWnd, out procId);
            var proc = Process.GetProcessById((int)procId);
            //Console.WriteLine(title);
            //Console.WriteLine(GetWindowTitle());

            if (!proc.MainWindowTitle.Equals(title) && (!title.Equals("")&&!GetAppName().Equals("explorer") ))
            {
                return true;
            }
            else
            {
                return false;
            }
        }
        public static Bitmap CaptureActiveWindow()
        {
            //Debug.WriteLine(GetProcId());
            Debug.WriteLine(GetWindowTitle());
            return CaptureWindow(hWnd);
        }

        private static IntPtr GetActiveWindow()
        {
            IntPtr handle = IntPtr.Zero;
            return GetForegroundWindow();
        }

        public static Bitmap CaptureWindow(IntPtr handle)
        {
            var rect = new Rect();
            var rect1 = new Rect();
            var rect2 = new Rect();
            GetWindowRect(handle, ref rect);
            GetClientRect(handle, ref rect2);
            ClientToScreen(handle, ref rect1);
            int border_left = rect1.Left - rect.Left;
            int border_top = rect1.Top - rect.Top;
            //var bounds = new Rectangle(rect1.Left + rect2.Left, rect1.Top + rect2.Top, rect2.Right, rect2.Bottom);
            var bounds = new Rectangle(rect.Left, rect.Top, rect.Right - rect.Left, rect.Bottom - rect.Top);
            var result = new Bitmap(bounds.Width, bounds.Height);
            

            using (var graphics = Graphics.FromImage(result))
            {
                graphics.CopyFromScreen(new Point(bounds.Left, bounds.Top), Point.Empty, bounds.Size);
            }



            //Console.WriteLine(rect.Left.ToString() + " " + rect.Top.ToString() + " " + rect.Right.ToString() + " " + rect.Bottom.ToString());
            //Console.WriteLine(rect1.Left.ToString() + " " + rect1.Top.ToString() + " " + rect1.Right.ToString() + " " + rect1.Bottom.ToString());
            //Console.WriteLine(rect2.Left.ToString() + " " + rect2.Top.ToString() + " " + rect2.Right.ToString() + " " + rect2.Bottom.ToString());
            //Console.WriteLine(bounds.Left.ToString() + " " + bounds.Top.ToString() + " " + bounds.Right.ToString() + " " + bounds.Bottom.ToString());



            return result;
        }
        public static string GetAppName()
        {
            hWnd = GetActiveWindow();
            uint procId = 0;
            GetWindowThreadProcessId(hWnd, out procId);
            var proc = Process.GetProcessById((int)procId);
            return proc.ProcessName;
        }
        public static string GetWindowTitle()
        {
            if (title.Equals(""))
            {
                //IntPtr hWnd = GetForegroundWindow();
                uint procId = 0;
                GetWindowThreadProcessId(hWnd, out procId);
                var proc = Process.GetProcessById((int)procId);
                title = proc.MainWindowTitle;
            }
            return title;
        }
        public static int GetProcId()
        {
            //IntPtr hWnd = GetForegroundWindow();
            uint procId = 0;
            GetWindowThreadProcessId(hWnd, out procId);
            return (int)procId;
        }
        public static string GetURL()
        {
            string url = "";
            title = "";
            //hWnd = GetForegroundWindow();
            uint procId = 0;
            GetWindowThreadProcessId(hWnd, out procId);
            var proc = Process.GetProcessById((int)procId);
            //Debug.WriteLine(proc.StartInfo.Arguments);
            //Debug.WriteLine("---------------8888------------");
            //Debug.WriteLine(getGenericFilePath((int)procId));
            //Debug.WriteLine("---------------8888------------");
            //Debug.WriteLine("Process : " + proc.ProcessName);
            //Debug.WriteLine("Filename : " + proc.MainModule.FileName.ToString());
            if (proc.ProcessName == "devenv")
                url = GetExplorer(hWnd.ToInt32());
            if (proc.ProcessName == "firefox")
                url = GetBrowserURL("firefox");
            if (proc.ProcessName == "opera")
                url = GetBrowserURL("opera");
            if (proc.ProcessName == "chrome")
                url = GetChormeURL("chrome");
            if (proc.ProcessName == "iexplore")
                url = GetIEURL();
            if (proc.ProcessName == "explorer")
            {
                url = GetExplorer(hWnd.ToInt32());
                title = url;
            }
            if (proc.ProcessName.ToLower() == "winword")
            {
                try
                {
                    Microsoft.Office.Interop.Word.Application WordObj;
                    WordObj = (Microsoft.Office.Interop.Word.Application)System.Runtime.InteropServices.Marshal.GetActiveObject("Word.Application");
                    url = WordObj.ActiveDocument.FullName;
                    //Console.WriteLine(WordObj.ActiveDocument.FullName);
                }
                catch (Exception e) { Debug.WriteLine(e.ToString()); }
            }
            if (proc.ProcessName.ToLower() == "excel")
            {
                try
                {
                    Microsoft.Office.Interop.Excel.Application ExcelObj;
                    ExcelObj = (Microsoft.Office.Interop.Excel.Application)System.Runtime.InteropServices.Marshal.GetActiveObject("Excel.Application");
                    url = ExcelObj.ActiveWorkbook.FullName;
                    //Console.WriteLine(ExcelObj.ActiveWorkbook.FullName);
                }
                catch (Exception e) { Debug.WriteLine(e.ToString()); }
            }
            if (proc.ProcessName.ToLower() == "powerpnt")
            {
                try
                {
                    Microsoft.Office.Interop.PowerPoint.Application PptObj;
                    PptObj = (Microsoft.Office.Interop.PowerPoint.Application)System.Runtime.InteropServices.Marshal.GetActiveObject("PowerPoint.Application");
                    url = PptObj.ActivePresentation.FullName;
                    //Console.WriteLine(PptObj.ActivePresentation.FullName);
                }
                catch (Exception e) { Debug.WriteLine(e.ToString()); }
            }

            if (proc.ProcessName.ToLower() == "outlook")
            {
                Microsoft.Office.Interop.Outlook.Application OutlookObj = null;
                try
                {
                    OutlookObj = (Microsoft.Office.Interop.Outlook.Application)System.Runtime.InteropServices.Marshal.GetActiveObject("Outlook.Application");
                    Microsoft.Office.Interop.Outlook.MAPIFolder selectedFolder = OutlookObj.Application.ActiveExplorer().CurrentFolder;
                    
                    if (OutlookObj.Application.ActiveExplorer().Selection.Count > 0)
                    {
                        Object selObject = OutlookObj.Application.ActiveExplorer().Selection[1];
                        if (selObject is Microsoft.Office.Interop.Outlook.MailItem)
                        {
                            Microsoft.Office.Interop.Outlook.MailItem mailItem =
                                (selObject as Microsoft.Office.Interop.Outlook.MailItem);
                            title = mailItem.Subject;
                            url = mailItem.EntryID;
                            //mailItem.Display(false);
                        }
                        else if (selObject is Microsoft.Office.Interop.Outlook.ContactItem)
                        {
                            Microsoft.Office.Interop.Outlook.ContactItem contactItem =
                                (selObject as Microsoft.Office.Interop.Outlook.ContactItem);
                            title = contactItem.Subject;
                            url = contactItem.EntryID;
                        }
                        else if (selObject is Microsoft.Office.Interop.Outlook.AppointmentItem)
                        {
                            Microsoft.Office.Interop.Outlook.AppointmentItem apptItem =
                                (selObject as Microsoft.Office.Interop.Outlook.AppointmentItem);
                            title = apptItem.Subject;
                            url = apptItem.EntryID;
                        }
                        else if (selObject is Microsoft.Office.Interop.Outlook.TaskItem)
                        {
                            Microsoft.Office.Interop.Outlook.TaskItem taskItem =
                                (selObject as Microsoft.Office.Interop.Outlook.TaskItem);
                            title = taskItem.Subject;
                            url = taskItem.EntryID;
                        }
                        else if (selObject is Microsoft.Office.Interop.Outlook.MeetingItem)
                        {
                            Microsoft.Office.Interop.Outlook.MeetingItem meetingItem =
                                (selObject as Microsoft.Office.Interop.Outlook.MeetingItem);
                            title = meetingItem.Subject;
                            url = meetingItem.EntryID;
                        }
                    }
                }
                catch (Exception e) { Debug.WriteLine(e.ToString()); }
            }
            
            // Attempt to get generic path from a file if none of above not working
            if (url == "")
            {
                url = getGenericFilePath((int)procId);
            }

            if (url.Contains(".pdf"))
            {
                try
                {
                    Debug.WriteLine("THIS IS PDF FILE!!!!");
                    //Debug.WriteLine(GetWindowTitle());
                    if (GetWindowTitle().Contains(".pdf"))
                    {
                        //Debug.WriteLine(GetWindowTitle().Split(new string[] { ".pdf" }, StringSplitOptions.None)[0]);
                        if (!File.ReadAllText(@"source/AllFilePaths.txt").Trim().Equals(""))
                        {
                            string[] filepaths = File.ReadAllText(@"source/AllFilePaths.txt").Split(';');
                            for (int i = filepaths.Length - 1; i >= 0; i--)
                            {
                                if (filepaths[i].Contains(GetWindowTitle().Split(new string[] { ".pdf" }, StringSplitOptions.None)[0]))
                                {
                                    url = filepaths[i];
                                    break;
                                }
                            }
                        }
                    }
                    else
                    {
                        url = "";
                    }
                }
                catch(Exception exception)
                {
                    WriteToFile("source/logs.txt", DateTime.Now.ToString() + " : " + exception.ToString());

                }
            }

            Debug.WriteLine(url);
            return url;
        }

        private static string getGenericFilePath(int processId)
        {
            string path = "";
            try
            {
                string wmiQuery = string.Format("select CommandLine from Win32_Process where ProcessId={0}", processId);
                ManagementObjectSearcher searcher = new ManagementObjectSearcher(wmiQuery);
                ManagementObjectCollection retObjectCollection = searcher.Get();

                foreach (ManagementObject retObject in retObjectCollection)
                {
                    string CommandLine = retObject["CommandLine"].ToString();
                    path = CommandLine.Substring(CommandLine.IndexOf(" ") + 1, CommandLine.Length - CommandLine.IndexOf(" ") - 1);
                    if (path.Contains('"'))
                    {
                        string[] s_list = path.Split('\"');
                        path = s_list[s_list.Length - 2];
                    }
                }

                if (path.ToLower().Contains(".exe"))
                {
                    path = "";
                }
            }
            catch (Exception exception)
            {
                WriteToFile("source/logs.txt", DateTime.Now.ToString() + " : " + exception.ToString());
            }
            return path;
            /*string wmiQuery = "select CommandLine from Win32_Process where ProcessId="+processId;
            using (ManagementObjectSearcher searcher = new ManagementObjectSearcher(wmiQuery))
            {
                using (ManagementObjectCollection retObjectCollection = searcher.Get())
                {
                    foreach (ManagementObject retObject in retObjectCollection)
                    {
                        if (retObject["CommandLine"] != null)
                        {
                            string s = (string.Format("[{0}]", retObject["CommandLine"]));
                            string k = "";
                            if (s.Contains('"'))
                            {
                                string[] s_list = s.Split('\"');
                                k = s_list[s_list.Length - 2];
                            }
                            else
                                k = s;
                            return k;
                        }
                        return null;
                    }
                    return null;
                }
            }*/
        }

        public static string GetChormeURL(string ProcessName)
        {
            /*string ret = "";
            Process[] procs = Process.GetProcessesByName(ProcessName);
            foreach (Process proc in procs)
            {
                // the chrome process must have a window
                if (proc.MainWindowHandle == IntPtr.Zero)
                {
                    continue;
                }
                //AutomationElement elm = AutomationElement.RootElement.FindFirst(TreeScope.Children,
                //         new PropertyCondition(AutomationElement.ClassNameProperty, "Chrome_WidgetWin_1"));
                // find the automation element
                AutomationElement elm = AutomationElement.FromHandle(proc.MainWindowHandle);

                // manually walk through the tree, searching using TreeScope.Descendants is too slow (even if it's more reliable)
                AutomationElement elmUrlBar = null;
                try
                {
                    // walking path found using inspect.exe (Windows SDK) for Chrome 43.0.2357.81 m (currently the latest stable)
                    // Inspect.exe path - C://Program files (X86)/Windows Kits/10/bin/x64
                    var elm1 = elm.FindFirst(TreeScope.Children, new PropertyCondition(AutomationElement.NameProperty, "Google Chrome"));
                    if (elm1 == null) { continue; } // not the right chrome.exe
                    var elm2 = TreeWalker.RawViewWalker.GetLastChild(elm1); // I don't know a Condition for this for finding
                    var elm3 = elm2.FindFirst(TreeScope.Children, new PropertyCondition(AutomationElement.NameProperty, ""));
                    var elm4 = TreeWalker.RawViewWalker.GetNextSibling(elm3); // I don't know a Condition for this for finding
                    var elm5 = elm4.FindFirst(TreeScope.Children, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.ToolBar));
                    var elm6 = elm5.FindFirst(TreeScope.Children, new PropertyCondition(AutomationElement.NameProperty, ""));
                    elmUrlBar = elm6.FindFirst(TreeScope.Children, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit));
                }
                catch
                {
                    // Chrome has probably changed something, and above walking needs to be modified. :(
                    // put an assertion here or something to make sure you don't miss it
                    continue;
                }

                // make sure it's valid
                if (elmUrlBar == null)
                {
                    // it's not..
                    continue;
                }

                // elmUrlBar is now the URL bar element. we have to make sure that it's out of keyboard focus if we want to get a valid URL
                if ((bool)elmUrlBar.GetCurrentPropertyValue(AutomationElement.HasKeyboardFocusProperty))
                {
                    continue;
                }

                // there might not be a valid pattern to use, so we have to make sure we have one
                AutomationPattern[] patterns = elmUrlBar.GetSupportedPatterns();
                if (patterns.Length == 1)
                {
                    try
                    {
                        ret = ((ValuePattern)elmUrlBar.GetCurrentPattern(patterns[0])).Current.Value;
                        return ret;
                    }
                    catch { }
                    if (ret != "")
                    {
                        // must match a domain name (and possibly "https://" in front)
                        //if (Regex.IsMatch(ret, @"^(https:\/\/)?[a-zA-Z0-9\-\.]+(\.[a-zA-Z]{2,4}).*$"))
                        //{
                            // prepend http:// to the url, because Chrome hides it if it's not SSL
                            if (!ret.StartsWith("http"))
                            {
                                ret = "http://" + ret;
                            }
                            return ret;
                        //}
                    }
                    continue;
                }
            }
            return ret;*/
            string vp = "";
            Process[] procs = Process.GetProcessesByName(ProcessName);
            foreach (Process proc in procs)
            {
                // the chrome process must have a window
                if (proc.MainWindowHandle == IntPtr.Zero)
                {
                    continue;
                }
                try
                {
                    AutomationElement element = AutomationElement.FromHandle(proc.MainWindowHandle);
                    if (element == null)
                        return null;

                    AutomationElementCollection edits5 = element.FindAll(TreeScope.Subtree, new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Edit));
                    AutomationElement edit = edits5[0];
                    vp = ((ValuePattern)edit.GetCurrentPattern(ValuePattern.Pattern)).Current.Value as string;
                    //Debug.WriteLine(vp);
                    return vp;
                }
                catch (Exception e)
                {

                }
            }
            return vp;
        }
        private static string GetIEURL()
        {
            try
            {
                SHDocVw.InternetExplorer browser;
                string myLocalLink = "";
                mshtml.IHTMLDocument2 myDoc;
                SHDocVw.ShellWindows shellWindows = new SHDocVw.ShellWindows();
                string filename;
                foreach (SHDocVw.InternetExplorer ie in shellWindows)
                {
                    filename = System.IO.Path.GetFileNameWithoutExtension(ie.FullName).ToLower();
                    if ((filename == "iexplore"))
                    {
                        browser = ie;
                        myDoc = browser.Document;
                        myLocalLink = myDoc.url;
                    }
                }
                return myLocalLink;
            }
            catch
            {
                return null;
            }
        }
        private static string GetBrowserURL(string browser)
        {
            if (browser.Equals("firefox"))
            {
                try
                {
                    string url = QueryResult("SELECT url FROM moz_places WHERE title = '" + GetWindowTitle() + "' ");
                    Debug.WriteLine(url);
                    return url;
                }
                catch (Exception exception)
                {
                    WriteToFile("source/logs.txt", DateTime.Now.ToString() + " : " + exception.ToString());
                    return "";
                }
            }
            else
            {
                try
                {
                    string url = "";

                    Process[] procsOpera = Process.GetProcessesByName("opera");
                    foreach (Process opera in procsOpera)
                    {
                        // the chrome process must have a window
                        if (opera.MainWindowHandle == IntPtr.Zero)
                        {
                            continue;
                        }

                        // find the automation element
                        AutomationElement elm = AutomationElement.FromHandle(opera.MainWindowHandle);
                        AutomationElement elmUrlBar = elm.FindFirst(TreeScope.Descendants,
                            new PropertyCondition(AutomationElement.NameProperty, "Address field"));

                        // if it can be found, get the value from the URL bar
                        if (elmUrlBar == null) continue;

                        AutomationPattern pattern = elmUrlBar.GetSupportedPatterns().FirstOrDefault(wr => wr.ProgrammaticName == "ValuePatternIdentifiers.Pattern");

                        if (pattern == null) continue;

                        ValuePattern val = (ValuePattern)elmUrlBar.GetCurrentPattern(pattern);
                        url = val.Current.Value;
                        break;
                    }

                    return url;
                }
                catch
                {
                    return null;
                }
            }
        }
        private static string GetExplorer(int hwndId)
        {
            try
            {
                string path = "";
                foreach (SHDocVw.InternetExplorer window in new SHDocVw.ShellWindows())
                {
                    //Debug.WriteLine(window.HWND);
                    if (hwndId == window.HWND)
                    {
                        try
                        {
                            path = new Uri(window.LocationURL).LocalPath;
                        }
                        catch
                        {
                            return null;
                        }
                        break;
                    }
                }
                return path;
            }
            catch
            {
                return null;
            }
        }
        private static void WriteToFile(string path, string text)
        {
            using (StreamWriter sw = new StreamWriter(path, true))
            {
                sw.WriteLine(text);
                sw.Close();
            }
        }
    }
}