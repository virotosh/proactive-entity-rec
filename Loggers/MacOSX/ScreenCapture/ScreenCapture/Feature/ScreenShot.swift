//
//  ScreenShot.swift
//  ScreenCapture
//
//  Created by kin on 12/27/16.
//  Copyright © 2016 Vuong, Thanh T. All rights reserved.
//

import Cocoa
import Foundation
import Quartz

class ScreenShot: NSObject {
    var wnumber = Int()
    var wtitle = String("")
    var appname = String("")
    //var url = String("")
    
    override init(){
        
    }
    
    deinit{
        print("Release object \(wnumber)")
    }
    
    func screenShot(fname: String) -> Void{
        // Capture active window screen by window number
        var cgImage = CGWindowListCreateImage(CGRectNull, CGWindowListOption.OptionIncludingWindow, CGWindowID(self.wnumber), CGWindowImageOption.BoundsIgnoreFraming)
        let cropRect = CGRectMake(0, 0, CGFloat(CGImageGetWidth(cgImage)), CGFloat(CGImageGetHeight(cgImage)) - 0)
        cgImage = CGImageCreateWithImageInRect(cgImage, cropRect)
        if cgImage == nil {
            print("null")
            return
        }
        // Create a bitmap rep from the image...
        let bitmapRep = NSBitmapImageRep(CGImage: cgImage!)
        // Save the file
        let newRep = bitmapRep.bitmapImageRepByConvertingToColorSpace(NSColorSpace.genericGrayColorSpace(), renderingIntent: NSColorRenderingIntent.Default)
        let data = newRep!.representationUsingType(NSBitmapImageFileType.NSJPEGFileType, properties: [NSImageCompressionFactor: 1])
        
        data!.writeToFile(fname, atomically: false)
    }
    
    func getTitle() -> String{
        //var wintitle = String("")
        if wtitle == "" || self.appname == "Mail" || self.appname == "Microsoft Outlook"
        {
            let applescript = DoAppleScript(applicationName: self.appname)
            do{
                wtitle = try applescript.getActiveWindowTitle()
            }
            catch {}
            
        }

        return wtitle
    }
    
    func getAppName() -> String{
        return appname
    }
    
    func getURL() -> String{
        var url = String("")
        let applescript = DoAppleScript(applicationName: self.appname)
        
        do{
            url = try applescript.getURL(self.wtitle)
        }
        catch {}
        
        return url
    }
    
    func initializeScreenshotParameters() -> Void{
        // Get active window number
        
        let workspace = NSWorkspace.sharedWorkspace()
        let activeApps = workspace.runningApplications
        for app in activeApps {
            if app.active{
                let options = CGWindowListOption(arrayLiteral: CGWindowListOption.ExcludeDesktopElements, CGWindowListOption.OptionOnScreenOnly)
                let windowListInfo = CGWindowListCopyWindowInfo(options, CGWindowID(0))
                let infoList = windowListInfo as NSArray? as? [[String: AnyObject]]
                for window in infoList! {
                    if let data = window as? NSDictionary
                    {
                        let winid = data.objectForKey("kCGWindowLayer")!
                        let wnumber = data.objectForKey("kCGWindowNumber")!
                        let winname = (data.objectForKey("kCGWindowName") != nil) ? data.objectForKey("kCGWindowName")! as! String : ""
                        let ownername = (data.objectForKey("kCGWindowOwnerName") != nil) ? data.objectForKey("kCGWindowOwnerName") as! String : ""
                        if ownername == app.localizedName && data.objectForKey("kCGWindowAlpha")! as! NSObject == 1 && winid as! NSObject == 0 {
                            //print(window)
                            self.wnumber = Int("\(wnumber as! NSObject)")!
                            self.wtitle = winname
                            self.appname = ownername
                            //print(winname)
                            if self.appname == "Mail" || self.appname == "Microsoft Outlook"{
                                self.wtitle = getTitle()
                            }
                            if winname != "" {
                                break
                            }
                        }
                    }
                }
                break
            }
        }
    }
}
