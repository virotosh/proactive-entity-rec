//
//  AppDelegate.swift
//  LauncherApplication
//
//  Created by kin on 12/29/16.
//  Copyright © 2016 Vuong, Thanh T. All rights reserved.
//

import Cocoa

@NSApplicationMain
class AppDelegate: NSObject, NSApplicationDelegate {



    func applicationDidFinishLaunching(aNotification: NSNotification) {
        let mainAppIdentifier = "UH.ScreenCapture"
        let running = NSWorkspace.sharedWorkspace().runningApplications
        var alreadyRunning = false
        
        for app in running{
            //print(app.bundleIdentifier)
            if app.bundleIdentifier == mainAppIdentifier {
                alreadyRunning = true
                break
            }
        }
        
        if !alreadyRunning{
            NSDistributedNotificationCenter.defaultCenter().addObserver(self, selector: "terminate", name: "killme", object: mainAppIdentifier)
            let path = NSBundle.mainBundle().bundlePath as NSString
            var components = path.pathComponents
            
            components.removeLast()
            components.removeLast()
            components.removeLast()
            //components.removeAll()
            //components.append("/")
            //components.append("Applications")
            components.append("MacOS")
            components.append("ScreenCapture")
            
            let newPath = NSString.pathWithComponents(components)
            NSWorkspace.sharedWorkspace().launchApplication(newPath)
        }
        else
        {
            self.terminate()
        }
    }
    
    func terminate(){
        NSApp.terminate(nil)
    }

    func applicationWillTerminate(aNotification: NSNotification) {
        // Insert code here to tear down your application
    }


}

