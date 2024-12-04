using Microsoft.Win32;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SQLite;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Surveillance
{
    public class HistoryItem
    {
        public string URL { get; set; }

        public string Title { get; set; }

        public DateTime VisitedTime { get; set; }
    }
    public class AccessInfo
    {
        public string Name { get; set; }

        public string IsFiltered { get; set; }
    }
    class MyUtil
    {
        public MyUtil()
        {

        }
        public AccessInfo[] getAppsFromFile()
        {
            AccessInfo[] appList = new AccessInfo[] { };
            try
            {
                // deserialize JSON directly from a file
                using (StreamReader file = File.OpenText(@"source/appACL.txt"))
                {
                    JsonSerializer serializer = new JsonSerializer();
                    appList = (AccessInfo[])serializer.Deserialize(file, typeof(AccessInfo[]));
                }
            }
            catch (Exception e) { }
            return appList;
        }
        public AccessInfo[] getChromeHistoryFromFile()
        {
            AccessInfo[] allHistoryItems = new AccessInfo[] { };
            try
            {
                // deserialize JSON directly from a file
                using (StreamReader file = File.OpenText(@"source/chromeACL.txt"))
                {
                    JsonSerializer serializer = new JsonSerializer();
                    allHistoryItems = (AccessInfo[])serializer.Deserialize(file, typeof(AccessInfo[]));
                }
            }
            catch (Exception e) { }
            return allHistoryItems;
        }
        public AccessInfo[] getApps()
        {
            List<String> appList = new List<String>();
            try
            {
                // search in: CurrentUser
                string registry_key = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall";
                using (Microsoft.Win32.RegistryKey key = Registry.CurrentUser.OpenSubKey(registry_key))
                {
                    foreach (string subkey_name in key.GetSubKeyNames())
                    {
                        using (RegistryKey subkey = key.OpenSubKey(subkey_name))
                        {
                            string desc = (string)subkey.GetValue("DisplayName");
                            string installPath = (string)subkey.GetValue("InstallLocation");
                            if (!string.IsNullOrEmpty(desc) && !string.IsNullOrEmpty(installPath))
                            //if (!string.IsNullOrEmpty(desc))
                            {
                                try
                                {
                                    if (!appList.Contains(desc))
                                        appList.Add(desc);
                                    //Debug.WriteLine("------");
                                    //Debug.WriteLine(desc + installPath);
                                    //Debug.WriteLine(GetFileExeNameByFileDescription(desc, installPath));
                                    //Debug.WriteLine("------");
                                }
                                catch (Exception e)
                                {
                                    Debug.WriteLine(e.ToString());
                                }
                            }
                        }
                    }
                }

                // search in: LocalMachine_32
                registry_key = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall";
                using (Microsoft.Win32.RegistryKey key = Registry.LocalMachine.OpenSubKey(registry_key))
                {
                    foreach (string subkey_name in key.GetSubKeyNames())
                    {
                        using (RegistryKey subkey = key.OpenSubKey(subkey_name))
                        {
                            string desc = (string)subkey.GetValue("DisplayName");
                            string installPath = (string)subkey.GetValue("InstallLocation");
                            if (!string.IsNullOrEmpty(desc) && !string.IsNullOrEmpty(installPath))
                            //if (!string.IsNullOrEmpty(desc))
                            {
                                try
                                {
                                    if (!appList.Contains(desc))
                                        appList.Add(desc);
                                }
                                catch (Exception e)
                                {
                                    Debug.WriteLine(e.ToString());
                                }
                            }
                        }
                    }
                }

                // search in: LocalMachine_64
                registry_key = @"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall";
                using (Microsoft.Win32.RegistryKey key = Registry.LocalMachine.OpenSubKey(registry_key))
                {
                    foreach (string subkey_name in key.GetSubKeyNames())
                    {
                        using (RegistryKey subkey = key.OpenSubKey(subkey_name))
                        {
                            string desc = (string)subkey.GetValue("DisplayName");
                            string installPath = (string)subkey.GetValue("InstallLocation");
                            if (!string.IsNullOrEmpty(desc) && !string.IsNullOrEmpty(installPath))
                            //if (!string.IsNullOrEmpty(desc))
                            {
                                try
                                {
                                    if (!appList.Contains(desc))
                                        appList.Add(desc);
                                }
                                catch (Exception e)
                                {
                                    Debug.WriteLine(e.ToString());
                                }
                            }
                        }
                    }
                }
            }
            catch (Exception e) { }
            String[] appNames = appList.ToArray();
            Array.Sort(appNames, StringComparer.InvariantCulture);

            List<AccessInfo> apps = new List<AccessInfo>();
            foreach (String name in appNames)
            {
                AccessInfo appItem = new AccessInfo()
                {
                    Name = name,
                    IsFiltered = "0"

                };
                apps.Add(appItem);
            }

            return apps.ToArray();
        }

        public List<HistoryItem> getChromeHistory()
        {
            List<HistoryItem> allHistoryItems = new List<HistoryItem>();
            try
            {
                string chromeHistoryFile = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData)
                + @"\Google\Chrome\User Data\Default\History";
                if (File.Exists(chromeHistoryFile))
                {
                    SQLiteConnection connection = new SQLiteConnection
                    ("Data Source=" + chromeHistoryFile + ";Version=3;New=False;Compress=True;");

                    connection.Open();

                    DataSet dataset = new DataSet();

                    SQLiteDataAdapter adapter = new SQLiteDataAdapter
                    ("select * from urls order by last_visit_time desc", connection);

                    adapter.Fill(dataset);

                    if (dataset != null && dataset.Tables.Count > 0 & dataset.Tables[0] != null)
                    {
                        DataTable dt = dataset.Tables[0];


                        foreach (DataRow historyRow in dt.Rows)
                        {
                            HistoryItem historyItem = new HistoryItem()
                            {
                                URL = Convert.ToString(historyRow["url"]),
                                Title = Convert.ToString(historyRow["title"])

                            };

                            // Chrome stores time elapsed since Jan 1, 1601 (UTC format) in microseconds
                            long utcMicroSeconds = Convert.ToInt64(historyRow["last_visit_time"]);

                            // Windows file time UTC is in nanoseconds, so multiplying by 10
                            DateTime gmtTime = DateTime.FromFileTimeUtc(10 * utcMicroSeconds);

                            // Converting to local time
                            DateTime localTime = TimeZoneInfo.ConvertTimeFromUtc(gmtTime, TimeZoneInfo.Local);
                            historyItem.VisitedTime = localTime;

                            allHistoryItems.Add(historyItem);
                        }
                    }
                }
            }
            catch (Exception e) { }

            return allHistoryItems;
        }

        public void WriteToFile(string path, string text)
        {
            try
            {
                using (StreamWriter sw = new StreamWriter(path, false))
                {
                    sw.WriteLine(text);
                    sw.Close();
                }
            }
            catch (Exception e) { }
        }
    }
}
