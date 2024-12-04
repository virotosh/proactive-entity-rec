//
//  AppDelegate.swift
//  ScreenCapture
//
//  Created by Vuong, Thanh T on 26/10/16.
//  Copyright © 2016 Vuong, Thanh T. All rights reserved.
//

import Cocoa
import Foundation
import AppKit
import ServiceManagement


@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {

    @IBOutlet weak var window: NSWindow!
    
    // DEFAULT SETTINGS
    var interval_forsenddata = 1
    var interval_captureshot = 2
    var interval_captureshot_during_idle = 3
    var interval_eyebud = 0
    var backend_address = String("http://reknowdesktopsurveillance.hiit.fi");
    var ignore_app = String("")
    var ignore_window_withtitle = String("")
    var labMode = false;
    var queuefolder = String("")
    var amountOfKeystroke = Int(0)
    
    ///////////
    let statusItem = NSStatusBar.systemStatusBar().statusItemWithLength(-2)
    var countdown_forscreenshot = 0
    var countdown_forsenddata = 0
    weak var timer_forscreenshot: NSTimer? = NSTimer()
    var timer_forsenddata: NSTimer? = NSTimer()
    var licenseid = String("")
    var lang = String("")
    var waitForResponse = Bool(false)
    var LOG_CONDITION = Bool(true)
    var isIdle = Bool(true)
    // Popup menu
    let popover = NSPopover()
    let notification = QuotesViewController()
    var eventMonitor: EventMonitor?
    
    // ScreenShot class
    let screen = ScreenShot()
    // Application Support and Log Directory
    var applicationSupportDirectory = String("")
    var applicationLogDirectory = String("")
    // Acccessability enable params
    var accessibilityEnabled = Bool(false)
    var alertAccessabilityEnabledDispatched = Bool(false)
    let alertMsgForAccessabilityEnabled = NSAlert()
    
    // MAIN FUNCTION
    func applicationDidFinishLaunching(aNotification: NSNotification) {
        
        //Launcher Application setting
        let launcherAppIdentifier = "VK.LauncherApplication"
        //set launcher to login items for auto turn on upon start up
        let ret = SMLoginItemSetEnabled(launcherAppIdentifier, true)
        /*let running = NSWorkspace.sharedWorkspace().runningApplications
        var alreadyRunning = false
        let mainAppIdentifier = "UH.ScreenCapture"
        
        for app in running{
            if app.bundleIdentifier == mainAppIdentifier {
            //print(app.bundleIdentifier)
            }
        }*/
        //let path = NSBundle.mainBundle().bundlePath as NSString
        //var components = path.pathComponents
        var startedAtLogin = false
        for app in NSWorkspace.sharedWorkspace().runningApplications{
            //self.writeLog(app.bundleIdentifier! as String)
            ////print(app.bundleURL)
            if app.bundleIdentifier == launcherAppIdentifier{
                ////print(app.bundleIdentifier)
                startedAtLogin = true
            }
        }
        
        if startedAtLogin{
            NSDistributedNotificationCenter.defaultCenter().postNotificationName("killme", object: NSBundle.mainBundle().bundleIdentifier!)
        }
        
        // Enable Accessibility params & Notification text
        accessibilityEnabled = AXIsProcessTrustedWithOptions(
            [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true])
        alertMsgForAccessabilityEnabled.messageText = "Please enable ScreenCapture Using Accessibility feature"
        alertMsgForAccessabilityEnabled.informativeText = "Please be aware that enable app in Accessibility will give permission to the app to monitor screen. The app DOES NOT record your keystroke, only to detect your keystroke anonymously as input signal to capture screenshots. You can enable ScreenCapture service in System Preferences->Security and Privacy -> Accessibility. And then press 'OK' "

        // popup menu params
        popover.contentViewController = notification
        eventMonitor = EventMonitor(mask:[.LeftMouseDownMask,.RightMouseDownMask]) { [unowned self] event in
            if self.popover.shown {
                self.closePopover(event)
            }
        }
        eventMonitor?.start()
        
        
        // Check Application Folder exist, Otherwise create a new file and generate a new folder
        applicationSupportDirectory = "\(NSSearchPathForDirectoriesInDomains(NSSearchPathDirectory.ApplicationSupportDirectory, NSSearchPathDomainMask.UserDomainMask, true).first!)/ScreenCapture"
        //print(applicationSupportDirectory)
        applicationLogDirectory = applicationSupportDirectory.stringByReplacingOccurrencesOfString("Application Support", withString: "Logs")
        // Check Support Folder exists
        checkSupportFolderExistence()
        
        // set screencapture logging software in idle mode
        setLoggingInIdleMode()
        timer_forscreenshot = NSTimer.scheduledTimerWithTimeInterval(1, target: self, selector: "doWaitToScrenshot", userInfo: nil, repeats: true)
        // periodically run timerAutoSendData function
        self.timer_forsenddata = NSTimer.scheduledTimerWithTimeInterval(1, target: self, selector: "timerAutoSendData", userInfo: nil, repeats: true)
        
        // User input mouse/keystroke event
        var inputEventMonitor: AnyObject!
        /// remove .ScrollWheelMask as scrolling gives too many screen captures
        inputEventMonitor = NSEvent.addGlobalMonitorForEventsMatchingMask((NSEventMask:[.KeyDownMask,.LeftMouseUpMask,.RightMouseUpMask,.OtherMouseUpMask,.ScrollWheelMask]), handler: {(event: NSEvent) -> Void in
//////////// MAIN LOGGING EVENT BASED ON USER INPUT ///////////////////////////////////////////
            // ASKING USER TO ENABLE SECURITY AND ACCESSIBILITY
            //self.accessibilityEnabled = AXIsProcessTrustedWithOptions(
                //[kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true])
            ////print("Accessability status: \(self.accessibilityEnabled)")
            //if !self.accessibilityEnabled {
            //    return
                
            //}
            
            
            if self.LOG_CONDITION {
                // wait until countdown_forscreenshot timer invalid
                if !self.isIdle && self.amountOfKeystroke>100 {
                    //print("input timer (not idle) still running")
                    //print(self.amountOfKeystroke)
                }
                else {
                    if event.type.rawValue == 10{
                        self.amountOfKeystroke++
                    }
                    // set countdown_forscreenshot, set to active mode
                    self.setLoggingInActiveMode()
                }
            }
///////////////////////////////////////////////////////////////////////////
        })
        
        // Create Pause/Resume button
        if let button = statusItem.button {
            button.image = NSImage(named: "ResumeButtonImage")
            button.toolTip = "The logger is RUNNING"
            // pause click event
            // Stop logging activity
            button.action = Selector("pauseOrResumeLog:")
        }
    }
    
    // set logging in idle mode
    func setLoggingInIdleMode() -> Void
    {
        print("idle")
        isIdle = Bool(true)
        countdown_forscreenshot = self.interval_captureshot_during_idle
    }
    
    // set logging in active mode
    func setLoggingInActiveMode() -> Void
    {
        //print("Active")
        isIdle = Bool(false)
        countdown_forscreenshot = self.interval_captureshot
    }
    
    // Check pre-defined window titles (in setting file) to be ignored / no screenshots
    func isWindowTitleIgnored(screenWindowTitle:String) -> Bool
    {
        let exceptionalWindows = ignore_window_withtitle.componentsSeparatedByString("-")
        if exceptionalWindows.contains(screenWindowTitle) && screenWindowTitle != "" {
            return true
        }
        return false;
    }
    
    // Check pre-defined applications (in setting file) to be ignored / no screenshots
    func isApplicationIgnored(screenApplication:String) -> Bool
    {
        let exceptionalApplications = ignore_app.componentsSeparatedByString("-")
        let filteredStrings = exceptionalApplications.filter({(item: String) -> Bool in
            let stringMatch = screenApplication.lowercaseString.rangeOfString(item.lowercaseString)
            return stringMatch != nil ? true : false
        })
        if filteredStrings.count>0 && screenApplication != ""{
            return true
        }
        return false;
    }
    
    // Load settings of the setting.txt file
    func loadSettings(data:String) -> Void
    {
        let settings = data.componentsSeparatedByCharactersInSet(NSCharacterSet.newlineCharacterSet())
        interval_forsenddata = Int(settings[0].componentsSeparatedByString(";")[1])!
        interval_captureshot = Int(settings[1].componentsSeparatedByString(";")[1])!
        lang = settings[2].componentsSeparatedByString(";")[1]
        backend_address = settings[3].componentsSeparatedByString(";")[1]
        ignore_app = settings[4].componentsSeparatedByString(";")[1]
        ignore_window_withtitle = settings[5].componentsSeparatedByString(";")[1]
        interval_captureshot_during_idle = Int(settings[6].componentsSeparatedByString(";")[1])!
        queuefolder = settings[7].componentsSeparatedByString(";")[1]
    }
    
    // Function to check if Suport Folder contains 3 needed folders: log (for any exceptions caused by the screencapturing software), temp, extra folder
    func checkSupportFolderExistence()
    {
        let filemanager:NSFileManager = NSFileManager()
        
        // Create ScreenCapture Folder in Application Support Folder.
        if !filemanager.fileExistsAtPath("\(applicationSupportDirectory)"){
            do {
                try filemanager.createDirectoryAtPath("\(applicationSupportDirectory)", withIntermediateDirectories: true, attributes: nil)
                //print("Support Folder created")
            }
            catch let error as NSError{
                // Exception
                writeLog("Can not create Support Folder \(error.localizedDescription)")
            }
        }
        // Create ScreenCapture Folder in Log Folder in Library.
        if !filemanager.fileExistsAtPath("\(applicationLogDirectory)"){
            do {
                try filemanager.createDirectoryAtPath("\(applicationLogDirectory)", withIntermediateDirectories: true, attributes: nil)
                //print("Log Folder created")
            }
            catch let error as NSError{
                // Exception
                writeLog("Can not create Log Folder \(error.localizedDescription)")
            }
        }
        
        var folders: [String] = ["tmp", "original", "oslog", "converted", "converted_withentities", "corpus", "language", "google", "persons", "keywords"]
        
        for folder in folders {
            if !filemanager.fileExistsAtPath("\(applicationSupportDirectory)/\(folder)"){
                do {
                    try filemanager.createDirectoryAtPath("\(applicationSupportDirectory)/\(folder)", withIntermediateDirectories: true, attributes: nil)
                }
                catch let error as NSError {
                    // Exception
                    writeLog("Can not create \(folder) Folder \(error.localizedDescription)")
                }
            }
        }
        
        // Create "lab" folder in ScreenCapture folder
        if !applicationSupportDirectory.containsString("/lab"){
            if !filemanager.fileExistsAtPath("\(applicationSupportDirectory)/lab"){
                do {
                    try filemanager.createDirectoryAtPath("\(applicationSupportDirectory)/lab", withIntermediateDirectories: true, attributes: nil)
                }
                catch let error as NSError {
                    // Exception
                    writeLog("Can not create lab Folder \(error.localizedDescription)")
                }
            }
            folders = ["tmp", "temp", "original", "oslog", "converted", "converted_withentities", "corpus", "language", "google", "persons", "keywords", "original_corpus", "user activity", "userlogs"]
            // Create all folders in lab folder
            for folder in folders {
                if !filemanager.fileExistsAtPath("\(applicationSupportDirectory)/lab/\(folder)"){
                    do {
                        try filemanager.createDirectoryAtPath("\(applicationSupportDirectory)/lab/\(folder)", withIntermediateDirectories: true, attributes: nil)
                    }
                    catch let error as NSError {
                        // Exception
                        writeLog("Can not create lab sub-\(folder) Folder \(error.localizedDescription)")
                    }
                }
            }
        }
        
        // Create Setting File if not exist
        if filemanager.fileExistsAtPath("\(applicationSupportDirectory)/setting.txt") {
            let data = try! NSString(contentsOfFile: "\(applicationSupportDirectory)/setting.txt", encoding: NSUTF8StringEncoding) as String
            // LOAD SETTINGS
            loadSettings(data)
            //print("Language File exists")
        } else {
            do {
                let setting = String("timedelaysendtoserver;5\ntimedelaycapturescreen;2\nlang;eng\nbackend;http://reknowdesktopsurveillance.hiit.fi\nexceptionapplication;\nexceptionwindowtitle;\nidlemode;30\nqueuefolder;01")
                try setting.writeToFile("\(self.applicationSupportDirectory)/setting.txt", atomically: true, encoding: NSUTF8StringEncoding)
                
                //LOAD SETTINGS AFTER CREATING setting.txt for first time usage
                let data = try! NSString(contentsOfFile: "\(applicationSupportDirectory)/setting.txt", encoding: NSUTF8StringEncoding) as String
                loadSettings(data)
            }
            catch let error as NSError {
                /* error handling here */
                self.writeLog("Can not write to setting.txt \(error.localizedDescription)")
            }
        }
        
        // Create License File if not exist (Mac address)
        if filemanager.fileExistsAtPath("\(applicationSupportDirectory)/LicenseID.txt") {
            licenseid = try! NSString(contentsOfFile: "\(applicationSupportDirectory)/LicenseID.txt", encoding: NSUTF8StringEncoding) as String
            //print("File exists")
        } else {
            //generate licenseid MAC address
            licenseid = Utility().macSerialNumber()!
            
            // Register LicenseID on system if not yet registered
            do {
                try self.licenseid.writeToFile("\(self.applicationSupportDirectory)/LicenseID.txt", atomically: true, encoding: NSUTF8StringEncoding)
            }
            catch let error as NSError {
                /* error handling here */
                self.writeLog("Can not write to LicenseID.txt \(error.localizedDescription)")
            }
        }
    }
    
    /// Wait for X seconds and fire screenshot
    func doWaitToScrenshot() {
        // WHen countdown / delay at X seconds is over, capture screen of active window
        if countdown_forscreenshot == 0 {
            let priority = DISPATCH_QUEUE_PRIORITY_DEFAULT
            // Record all computer logs
            var screenshotName = "\(NSDate().timeIntervalSince1970)"
            // IMPORTANT: TO GET WINDOW ID of active window
            self.screen.initializeScreenshotParameters()
            var logDataContent:Dictionary<String,String> = ["url":"",
                "appname":"",
                "title":"",
                "filename":"\(screenshotName)"]
            
            // SCREENSHOT here
            dispatch_async(dispatch_get_global_queue(priority, 0)) {
                screenshotName = self.isIdle ? screenshotName+"_idle" : screenshotName
                logDataContent["filename"] = screenshotName
                
                // Checking window title and application exception
                if !self.isWindowTitleIgnored(self.screen.getTitle()) && !self.isApplicationIgnored(self.screen.getAppName()){
                    self.screenShot(logDataContent)
                }
                // After screenshot, set isIdle to true.
                self.setLoggingInIdleMode()
                self.amountOfKeystroke = Int(0)
            }
        }
        else{
            //print("time elapsed for further INPUT \(countdown_forscreenshot)")
        }
        countdown_forscreenshot--
    }
    
    func dispatchAlert() -> Void{
        //NSRunningApplication.currentApplication().activateWithOptions(NSApplicationActivationOptions.ActivateIgnoringOtherApps)
        let response = alertMsgForAccessabilityEnabled.runModal()
        if (response == NSModalResponseCancel) {
            //print("Exit alertAccessabilityEnabledDispatched")
            alertAccessabilityEnabledDispatched = false
            self.countdown_forsenddata = self.interval_forsenddata
        }
        else
        {
            alertAccessabilityEnabledDispatched = true
        }
    }
    
    // Auto Send Data to BackEnd every X seconds (in setting file)
    func timerAutoSendData() {
        let priority = DISPATCH_QUEUE_PRIORITY_DEFAULT
        // If waiting time is over, start sending screenshot to the server
        if self.countdown_forsenddata == 0 {
            self.countdown_forsenddata--
            
            // Check Support Folder exists & Re-Load Settings (in case setting changes)
            checkSupportFolderExistence()
                
            // loop through files not uploaded yet 10 files at a time
            let numberOfFiles = 2
            let filemanager:NSFileManager = NSFileManager()
            let files = filemanager.enumeratorAtPath("\(applicationSupportDirectory)/tmp/")
            var index = 0
                
            dispatch_async(dispatch_get_global_queue(priority, 0)) {
                //Iterate through log folder
                do
                {
                        while let file = files?.nextObject() {
                            if NSFileManager.defaultManager().fileExistsAtPath("\(self.applicationSupportDirectory)/oslog/"+file.stringByReplacingOccurrencesOfString(".jpeg", withString: ".txt")) {
                                if index < numberOfFiles && file.hasSuffix("jpeg") {
                                    // counter just to see how long it takes to send 1 file to backend
                                    var counter = 0
                                    let filename = file.stringByReplacingOccurrencesOfString(".jpeg", withString: "")
                                    // sending data to backend
                                    print("file: \(filename)")
                                    self.sendDataToServer(filename)
                                    while self.waitForResponse {
                                        print("SLEEP!!!!! \(counter)")
                                        sleep(1)
                                        counter++
                                    }
                                }
                            }
                            index++
                        }
                        self.countdown_forsenddata = self.interval_forsenddata
                }
                catch let error as NSError {
                    //print("--------------------------------\(error)")
                    self.writeLog("Server Unreachable \(error.localizedDescription)")
                    self.countdown_forsenddata = self.interval_forsenddata
                    self.setIconToWarning()
                }
            }
        }
        else{
            // Count down for sending data
            if self.countdown_forsenddata >= 0{
                //print("time elapsed for send data \(self.countdown_forsenddata)")
                self.countdown_forsenddata--
                
                if labMode {
                    // EYE BUD HERE
                    // Getting picture from eyebud
                    //print(self.interval_eyebud)
                    
                    if self.interval_eyebud > 9 {
                        print("BUILDING CORPUS FOR EYE BUD")
                        dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0)) {
                            Utility().runPythonInBackground(self.applicationSupportDirectory)
                        }
                        self.interval_eyebud = 0
                    }
                    
                    if self.interval_eyebud % 3 == 0 {
                        dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0)) {
                            self.sendDataToServer("http://108.128.153.197:8181/photo/BAN_V2/\(self.interval_eyebud)")
                        }
                        print(self.interval_eyebud)
                    }
                    self.interval_eyebud++
                }
            }
        }
    }
    
    /// function to capture screen and retrieve OS logs
    func screenShot(logDataContent: NSDictionary){
        // Take screenshot active window
        let screenshotName = logDataContent["filename"] as! String
        self.screen.screenShot("\(applicationSupportDirectory)/tmp/\(screenshotName).jpeg")
        do {
            // MAKE SURE screenshot file co-exist with log file
            let filemanager:NSFileManager = NSFileManager()
            if filemanager.fileExistsAtPath("\(applicationSupportDirectory)/tmp/\(screenshotName).jpeg") {
                var logDataContentToWrite:Dictionary<String,String> = logDataContent as! Dictionary<String, String>
                logDataContentToWrite["url"] = self.screen.getURL()
                logDataContentToWrite["appname"] = self.screen.getAppName()
                logDataContentToWrite["title"] = self.screen.getTitle()
                print(self.screen.getTitle())
                let json = try NSJSONSerialization.dataWithJSONObject(logDataContentToWrite, options: .PrettyPrinted)
                try (NSString(data: json, encoding: NSUTF8StringEncoding)! as String).writeToFile("\(applicationSupportDirectory)/oslog/\(screenshotName).txt", atomically: true, encoding: NSUTF8StringEncoding)
            }
        }
        catch let error as NSError {
            /* error handling here */
            writeLog("Error when create screenshots/logs \(error.localizedDescription)")
        }
        
    }
    
    // Function send screen captures to backend
    func sendDataToServer(var fname: String) {
        self.waitForResponse = true
        
        // data to be sent
        let OCRAPIurl = NSURL(string: "\(self.backend_address):8888")!
        
        let request = NSMutableURLRequest(URL: OCRAPIurl)
        request.timeoutInterval = 2000
        request.HTTPMethod = "POST"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        let session = NSURLSession.sharedSession()
        
        if labMode && fname.containsString("http"){
            let data = "{\"img_url\":\"\(fname)\", \"engine\":\"vision\"}"
            request.HTTPBody = data.dataUsingEncoding(NSUTF8StringEncoding)
            fname = "\(NSDate().timeIntervalSince1970)"
        } else{
            // Check co-existence of log file and screenshot
            let filemanager:NSFileManager = NSFileManager()
            if !filemanager.fileExistsAtPath("\(applicationSupportDirectory)/tmp/\(fname).jpeg") || !filemanager.fileExistsAtPath("\(applicationSupportDirectory)/oslog/\(fname).txt"){
                self.waitForResponse = false
                return
            }
            // Image file and parameters
            let image = NSImage(contentsOfFile: "\(applicationSupportDirectory)/tmp/\(fname).jpeg")
            var imageData = image!.TIFFRepresentation
            let imageRep = NSBitmapImageRep(data: imageData!)
            let compressionFactor = Double(0.5)
            let imageProps = [ NSImageCompressionFactor : compressionFactor ]
            imageData = imageRep!.representationUsingType(NSBitmapImageFileType.NSJPEGFileType, properties: imageProps)
            let imageBase64 = imageData?.base64EncodedStringWithOptions(NSDataBase64EncodingOptions(rawValue: 0))
            
            let data = "{\"img_base64\":\"\(imageBase64!)\", \"engine\":\"vision\"}"
            request.HTTPBody = data.dataUsingEncoding(NSUTF8StringEncoding)
            //print(request)
        }
        
        // Start data session
        let task = session.dataTaskWithRequest(request) {
            (
            let data, let response, let error) in

            guard let _:NSData = data, let _:NSURLResponse = response  where error == nil else {
                print("Server Unreachable")
                self.waitForResponse = false
                self.setIconToWarning()
                return
            }
            
            let dataString = NSString(data: data!, encoding: NSUTF8StringEncoding)
            // Do things when get response from the backend.
            var responseAsDict = Utility().convertStringToDictionary((dataString?.lowercaseString)!)
            var detectText = ""
            if !((responseAsDict!["annotations"]!) is NSNull) {
                if responseAsDict!["annotations"]![0]["description"]! != nil {
                    //detectText = responseAsDict!["annotations"]![0]["description"] as! String
                    //self.writeTextFile(detectText, folder: "converted", filename: logDataAsDict!["filename"] as! String)
                    self.writeTextFile(dataString as! String, folder: "\(self.applicationSupportDirectory)/google", filename: fname)
                }
            }
            if !((responseAsDict!["translation"]!) is NSNull) {
                detectText = responseAsDict!["translation"]! as! String
                self.writeTextFile(detectText, folder: "\(self.applicationSupportDirectory)/converted", filename: fname)
            }
            if !((responseAsDict!["tags"]!) is NSNull) {
                if responseAsDict!["tags"]!["language"]! != nil {
                    do{
                        let tagsAsJSON = try NSJSONSerialization.dataWithJSONObject(responseAsDict!["tags"]!, options: .PrettyPrinted)
                        let tagsAsText = (NSString(data: tagsAsJSON, encoding: NSUTF8StringEncoding)! as String)
                        self.writeTextFile(tagsAsText, folder: "\(self.applicationSupportDirectory)/language", filename: fname)
                        
                        var keywordsAsArray: [String] = []
                        var personsAsArray: [String] = []
                        
                        if responseAsDict!["tags"]!["keywords"]! != nil{
                            for key in responseAsDict!["tags"]!["keywords"] as! [[String: AnyObject]] {
                                for _ in 0..<(key["count"] as! Int) {
                                    keywordsAsArray.append(key["text"]!.stringByReplacingOccurrencesOfString(" ", withString: "_"))
                                }
                            }
                            keywordsAsArray = keywordsAsArray.sort(Utility().length)
                            keywordsAsArray = keywordsAsArray.reverse()
                            
                            for key in keywordsAsArray {
                                if detectText.containsString(key){
                                    detectText = detectText.stringByReplacingOccurrencesOfString(key, withString: "")
                                }
                            }
                        }
                        if responseAsDict!["tags"]!["entities"]! != nil{
                            for ent in responseAsDict!["tags"]!["entities"] as! [[String: AnyObject]] {
                                if ent["type"] as! String == "person"{
                                    for _ in 0..<(ent["count"] as! Int) {
                                        personsAsArray.append(ent["text"]!.stringByReplacingOccurrencesOfString(" ", withString: "_"))
                                    }
                                }
                            }
                            personsAsArray = personsAsArray.sort(Utility().length)
                            personsAsArray = personsAsArray.reverse()
                            
                            for per in personsAsArray {
                                if detectText.containsString(per){
                                    detectText = detectText.stringByReplacingOccurrencesOfString(per, withString: "")
                                }
                            }
                        }
                        
                        self.writeTextFile(detectText, folder: "\(self.applicationSupportDirectory)/converted_withentities", filename: fname)
                        let personsAsJSON = try NSJSONSerialization.dataWithJSONObject(personsAsArray, options: .PrettyPrinted)
                        let personsAsString = (NSString(data: personsAsJSON, encoding: NSUTF8StringEncoding)! as String)
                        self.writeTextFile(personsAsString, folder: "\(self.applicationSupportDirectory)/persons", filename: fname)
                        let keywordsAsJSON = try NSJSONSerialization.dataWithJSONObject(keywordsAsArray, options: .PrettyPrinted)
                        let keywordsAsString = (NSString(data: keywordsAsJSON, encoding: NSUTF8StringEncoding)! as String)
                        self.writeTextFile(keywordsAsString, folder: "\(self.applicationSupportDirectory)/keywords", filename: fname)
                    }
                    catch let error as NSError{
                        self.writeLog("Error mapping LogData to JSON Format \(error.localizedDescription)")
                    }
                }
            }
            else {
                self.writeLog("file not uploaded")
                self.writeLog(dataString! as String)
            }
            
            let fileManager = NSFileManager.defaultManager()
            do {
                try fileManager.moveItemAtPath("\(self.applicationSupportDirectory)/tmp/\(fname).jpeg", toPath: "\(self.applicationSupportDirectory)/original/\(fname).jpeg")
                if self.LOG_CONDITION{
                    if let button = self.statusItem.button {
                        button.image = NSImage(named: "ResumeButtonImage")
                        button.toolTip = "The logger is RUNNING"
                    }
                }
            }
            catch let error as NSError {
                self.writeLog("Error moving tmp/extra file \(error.localizedDescription)")
            }
            
            self.waitForResponse = false;
            
        }
        task.resume()
    }
    
    // change image button to pause or resume, RESET all to initial settings upon Pause or Resume screencapture software
    func pauseOrResumeLog(sender: AnyObject){
        ////print("pause clicked")
        self.countdown_forscreenshot = self.interval_captureshot
        self.countdown_forsenddata = self.interval_forsenddata
        self.timer_forscreenshot?.invalidate()
        self.timer_forsenddata?.invalidate()
        self.LOG_CONDITION = (self.LOG_CONDITION) ? false : true
        if let button = statusItem.button {
            button.image = (self.LOG_CONDITION) ? NSImage(named: "ResumeButtonImage") : NSImage(named: "PauseButtonImage")
            button.toolTip = (self.LOG_CONDITION) ? "The logger is RUNNING" : "The logger is STOPPED"
            // Logging resume/turn on
            if self.LOG_CONDITION{
                // Check Support Folder exists
                checkSupportFolderExistence()
                
                // set screencapture logging software in idle mode
                setLoggingInIdleMode()
                self.timer_forscreenshot = NSTimer.scheduledTimerWithTimeInterval(1, target: self, selector: "doWaitToScrenshot", userInfo: nil, repeats: true)
                // periodically run timerAutoSendData function
                self.timer_forsenddata = NSTimer.scheduledTimerWithTimeInterval(1, target: self, selector: "timerAutoSendData", userInfo: nil, repeats: true)
                
                // toggle popup status
                if popover.shown {
                    closePopover(sender)
                }
                
            }
            // logging pause
            else
            {
                self.timer_forsenddata?.invalidate()
                Utility().runPythonInBackground(applicationSupportDirectory)
                // toggle popup status
                if !popover.shown {
                    showPopover(sender)
                }
                //popover.showRelativeToRect(button.bounds, ofView: button, preferredEdge: NSRectEdge.MinY)
            }
        }
        
    }
    
    func setIconToWarning() -> Void {
        // SET ICON WARNING
        if self.LOG_CONDITION{
            if let button = self.statusItem.button {
                if(button.image != NSImage(named: "WarningButtonImage"))
                {
                    button.image = NSImage(named: "WarningButtonImage")
                    button.toolTip = "Server Unreachable"
                }
            }
        }
    }
    
    // Write to logs in case of exceptions
    func writeLog(text: String) -> Void{
        do {
            try text.writeToFile("\(self.applicationLogDirectory)/\(NSDate().timeIntervalSince1970).log", atomically: true, encoding: NSUTF8StringEncoding)
        }
        catch let error as NSError {
            /* error handling here */
        }
    }
    // Write to folder in case of exceptions
    func writeTextFile(text: String, folder: String, filename: String) -> Void{
        do {
            try text.writeToFile("\(folder)/\(filename).txt", atomically: true, encoding: NSUTF8StringEncoding)
        }
        catch let error as NSError {
            /* error handling here */
        }
    }
    
    // Mouse click to open menu on ScreenCapture application icon
    func showPopover(sender: AnyObject?) {
        if let button = statusItem.button {
            popover.showRelativeToRect(button.bounds, ofView: button, preferredEdge: NSRectEdge.MinY)
        }
        eventMonitor?.start()
    }
    
    // Mouse click to close menu on ScreenCapture application icon
    func closePopover(sender: AnyObject?) {
        popover.performClose(sender)
        eventMonitor?.stop()
    }
    
    func applicationWillTerminate(aNotification: NSNotification) {
        // Insert code here to tear down your application
    }

}

