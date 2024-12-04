//
//  DoAppleScript.swift
//  ScreenCapture
//
//  Created by kin on 12/27/16.
//  Copyright © 2016 Vuong, Thanh T. All rights reserved.
//

import Cocoa
import Foundation
import SQLite

class DoAppleScript: NSObject {
    var applicationName = String()
    var scriptObject = NSAppleScript()
    var applicationSupportFirefoxDirectory = "\(NSSearchPathForDirectoriesInDomains(NSSearchPathDirectory.ApplicationSupportDirectory, NSSearchPathDomainMask.UserDomainMask, true).first!)/Firefox/Profiles"
    
    required init(applicationName: String){
        self.applicationName = applicationName
    }
    
    deinit{
        //print("Release Apple Script Object \(applicationName)")
    }
    
    func getActiveWindowTitle() -> String{
        var active_window_title = String("")
        var script =  String("")
        script = "set windowTitle to \"\"\n" +
            "tell application \"System Events\"\n " +
            "set frontApp to first application process whose frontmost is true\n" +
            "set frontAppName to name of frontApp\n" +
            "tell process frontAppName\n" +
            "tell (1st window whose value of attribute \"AXMain\" is true)\n" +
            "set windowTitle to value of attribute \"AXTitle\"\n" +
            "end tell\n" +
            "end tell\n" +
            "end tell\n" +
        "get windowTitle"
        if self.applicationName == "Mail"{
            script = "tell application \"Mail\" \n" +
                "set selectedMessages to selection \n" +
                "set theMessage to item 1 of selectedMessages \n" +
                "set messageid to message id of theMessage \n" +
                "set titletext to \"\" & (subject of theMessage)\n" +
                "return titletext \n" +
            "end tell"
        }
        if self.applicationName == "Microsoft Outlook"{
            script = "tell application \"Microsoft Outlook\" \n" +
            "   set theMessage to first item of (get current messages) \n" +
            "   set theSubject to the subject of theMessage \n" +
            "end tell \n" +
            "get theSubject"
        }
        active_window_title = self.execute(script).stringByReplacingOccurrencesOfString("\n", withString: "")
        return active_window_title
    }
    
    func getURL(wtitle: String) -> String{
                
                
        
        var url = String("")
        var script = String("")
        var isDirectory = Bool(false)
        let scriptForSpotLight = "set spotlightquery to \"\(wtitle)\" \n" +
                                "set thefolders to {path to downloads folder, path to desktop folder, path to documents folder, path to movies folder, path to pictures folder, path to music folder} \n" +
                                "repeat with i in thefolders \n" +
                                    "set thepath to quoted form of POSIX path of i \n" +
                                    "set command to \"mdfind -onlyin \" & thepath & \" \" & spotlightquery \n" +
                                    "set filepath to (paragraphs of (do shell script command)) \n" +
                                    "if filepath is not equal to {} then \n" +
                                        "exit repeat \n" +
                                    "end if \n" +
                                "end repeat \n" +
                                "filepath's item 1"
        switch self.applicationName {
            case "Safari":
                script = "tell application \"Safari\" to return URL of front document"
            case "Google Chrome": //&& !(winname as! String == " ") ??
                script = "tell application \"Google Chrome\" to return URL of active tab of front window"
            case "Chromium":
                script = "tell application \"Chromium\" to return URL of active tab of front window"
            case "Preview":
                script = "tell application \"Preview\" to return path of document 1 as text"
                isDirectory = Bool(true)
            case "TextEdit":
                script = "tell application \"TextEdit\" to return path of document 1 as text"
                isDirectory = Bool(true)
            case "Adobe Reader":
                script = "tell application \"System Events\"\n" +
                    "    tell process \"Adobe Reader\"\n" +
                    "        set thefile to value of attribute \"AXDocument\" of front window\n" +
                    "    end tell\n" +
                    "end tell\n" +
                    "set o_set to offset of \"/Users\" in thefile\n" +
                    "set fixFile to characters o_set thru -1 of thefile\n" +
                    "set thefile to fixFile as string\n" +
                    "thefile"
                isDirectory = Bool(true)
            case "Mail":
                script = "tell application \"Mail\" \n" +
                    "set selectedMessages to selection \n" +
                    "set theMessage to item 1 of selectedMessages \n" +
                    "set messageid to message id of theMessage \n" +
                    "set urltext to \"message://\" & \"%3c\" & messageid & \"%3e\" \n" +
                    "return urltext \n" +
                    "end tell"
            case "Microsoft PowerPoint":
                script = "tell application \"Microsoft PowerPoint\"\n" +
                    "    (path of active presentation) & \"/\" & (name of active presentation)\n" +
                    "end tell\n" +
                    "get POSIX path of result"
                isDirectory = Bool(true)
            case "Microsoft Excel":
                script = "tell application \"Microsoft Excel\"\n" +
                    "    ((path of active workbook) as text) & \"/\" & ((name of active workbook) as text)\n" +
                    "end tell\n" +
                    "get POSIX path of result"
                isDirectory = Bool(true)
            case "Microsoft Word":
                script = "try\n" +
                    "        tell application \"System Events\" to tell process \"Microsoft Word\"\n" +
                    "            value of attribute \"AXDocument\" of window 1\n" +
                    "        end tell\n" +
                    "        do shell script \"x=\" & quoted form of result & \"\n" +
                    "        x=${x/#file:\\\\/\\\\/}\n" +
                    "        printf ${x//%/\\\\\\\\x}\"\n" +
                    "       on error \n" +
                    "       set t to \"\"\n" +
                    "end try"
                isDirectory = Bool(true)
            case "Microsoft Outlook":
                script = "tell application \"Microsoft Outlook\" \n" +
                         "   set theMessage to first item of (get current messages) \n" +
                         "   set theSubject to the id of theMessage \n" +
                         "end tell \n" +
                         "get theSubject"
                isDirectory = Bool(false)
            case "Finder":
                script = "tell application \"Finder\"\n" +
                    "set theWin to front window\n" +
                    "set thePath to (POSIX path of (target of theWin as alias))\n" +
                    "end tell"
                isDirectory = Bool(true)
            default:
                script = "set fileUrl to \"\"\n" +
                    "tell application \"System Events\"\n " +
                    "set frontApp to first application process whose frontmost is true\n" +
                    "set frontAppName to name of frontApp\n" +
                    "tell process frontAppName\n" +
                    "tell (1st window whose value of attribute \"AXMain\" is true)\n" +
                    "set fileUrl to value of attribute \"AXDocument\"\n" +
                    "end tell\n" +
                    "end tell\n" +
                    "end tell\n" +
                "get fileUrl"
                isDirectory = Bool(false)
        }
        
        url = self.execute(script).stringByReplacingOccurrencesOfString("\n", withString: "")
        if isDirectory {
            url = "file://\(url)"
        }
        
        if self.applicationName == "Firefox"{
            
            do{
                let filemanager = NSFileManager.defaultManager()
                let files = filemanager.enumeratorAtPath(applicationSupportFirefoxDirectory)
                var firefox_profile = String("")
                while let file = files?.nextObject() {
                    if ("\(file)".rangeOfString("places.sqlite") != nil){
                        firefox_profile = "\(file)"
                        break
                    }
                }
                let db = try Connection("\(applicationSupportFirefoxDirectory)/\(firefox_profile)")
                for row in try db.prepare("SELECT url FROM moz_places WHERE title='\(wtitle.stringByReplacingOccurrencesOfString(" - (Private Browsing)", withString: ""))'") {
                    url = "\(row[0]!)"
                    break
                }
                
            }catch let error as NSError {
                print(error.localizedDescription)
                
            }
        }
        
        return url
    }
    
    func execute(appScript: String) -> String {
        var error: NSDictionary?
        scriptObject = NSAppleScript(source: appScript)!
        let output = scriptObject.executeAndReturnError(&error)
        if(error != nil)
        {
            print("error: \(error)")
            return "error"
        }
        else
        {
            if output.stringValue != nil{
                return output.stringValue!
            }
            else
            {
                return ""
            }
        }
    }
    
    
    
}
