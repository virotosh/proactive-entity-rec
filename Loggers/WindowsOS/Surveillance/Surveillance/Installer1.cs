using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Configuration.Install;
using System.Linq;
using System.Threading.Tasks;
using System.Diagnostics;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;

namespace Surveillance
{
    [RunInstaller(true)]
    public partial class Installer1 : System.Configuration.Install.Installer
    {
        public Installer1()
        {
            InitializeComponent();
        }
        /*private void AfterInstallEventHandler(object sender, InstallEventArgs e)
        {
            // Add steps to perform any actions after the install process.
            //string LicenseID = Context.Parameters["ProductID"];
            String path = @"source/settings.txt";
            using (System.IO.StreamWriter sw = new System.IO.StreamWriter(path, true))
            {
                sw.Write("{\"backend\":\"upload.php\", \"lang\": \"eng+fin\", \"queuefolder\":\"16\"");
                sw.Close();
            }
        }*/
        public override void Install(IDictionary savedState)
        {
            base.Install(savedState);
            appUsage(Context);
            chromeUsage(Context);
            //AfterInstall += new InstallEventHandler(AfterInstallEventHandler);
            /*string LicenseID = Context.Parameters["ProductID"];
            //Add custom code here
            // Check key from server
            try
            {
                string url_req = "http://reknowdesktopsurveillance.hiit.fi:9200/licenses/_search?pretty=true&q=_id:" + LicenseID;
                //System.Windows.Forms.MessageBox.Show(url_req);
                using (var client = new System.Net.WebClient())
                {
                    Newtonsoft.Json.Linq.JObject result = Newtonsoft.Json.Linq.JObject.Parse(client.DownloadString(url_req));
                    if (result["hits"]["total"].ToString().Equals("1"))
                    {
                        string path = Context.Parameters["TARGETDIR"]+ "source/LicenseID.txt";
                        //System.Windows.Forms.MessageBox.Show(path);
                        using (System.IO.StreamWriter sw = new System.IO.StreamWriter(path,false))
                        {
                            sw.Write(LicenseID);
                            sw.Close();
                        }
                    }
                    else
                    {
                        throw new Exception("Invalid Key");
                    }
                }
            }
            catch (Exception e)
            {
                throw new Exception(e.ToString());
            }*/
        }

        public static void chromeUsage(InstallContext context)
        {
            try
            {
                List<HistoryItem> chromeitems = new MyUtil().getChromeHistory();

                List<String> chromehistory = new List<String>();
                foreach (HistoryItem h in chromeitems)
                {
                    Uri myUri = new Uri(h.URL);
                    string host = myUri.Host;
                    if (!chromehistory.Contains(host) && !string.IsNullOrEmpty(host))
                        chromehistory.Add(host);
                }

                String[] _chromehistory = chromehistory.ToArray();
                Array.Sort(_chromehistory, StringComparer.InvariantCulture);
                List<AccessInfo> chromeAccessInfo = new List<AccessInfo>();
                foreach (string name in _chromehistory)
                {
                    AccessInfo item = new AccessInfo()
                    {
                        Name = name,
                        IsFiltered = "0"
                    };
                    chromeAccessInfo.Add(item);
                }
                // Write to JSON
                //JObject chrome = JObject.FromObject(chromeitems);
                // Write extra info to files
                //String path = @"source/chromehistory.txt";
                String path = context.Parameters["TARGETDIR"] + "source/chromehistory.txt";
                //new MyUtil().WriteToFile(path, chrome.ToString());
                new MyUtil().WriteToFile(path, JsonConvert.SerializeObject(chromeitems).ToString());

                // Write to JSON
                path = context.Parameters["TARGETDIR"] + "source/chromeACL.txt";
                new MyUtil().WriteToFile(path, JsonConvert.SerializeObject(chromeAccessInfo).ToString());
            }
            catch (Exception e)
            {

            }
        }
        public static void appUsage(InstallContext context)
        {
            AccessInfo[] appNames = new MyUtil().getApps();

            // Write extra info to files
            String path = context.Parameters["TARGETDIR"] + "source/appACL.txt";
            new MyUtil().WriteToFile(path, JsonConvert.SerializeObject(appNames).ToString());
        }

        public override void Rollback(IDictionary savedState)
        {
            base.Rollback(savedState);
            //Add custom code here
        }

        public override void Commit(IDictionary savedState)
        {
            base.Commit(savedState);
            //Add custom code here
        }


        public override void Uninstall(IDictionary savedState)
        {
            Process application = null;
            foreach (var process in Process.GetProcesses())
            {
                if (!process.ProcessName.ToLower().Equals("surveillance")) continue;
                application = process;
                //break;
                if (application != null && application.Responding)
                {
                    application.Kill();
                    //base.Uninstall(savedState);
                }
            }

           // if (application != null && application.Responding)
            //{
               // application.Kill();
                base.Uninstall(savedState);
            //}
        }
    }
}
