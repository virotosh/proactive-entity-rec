//
//  QuotesViewController.swift
//  ScreenCapture
//
//  Created by kin on 12/27/16.
//  Copyright © 2016 Vuong, Thanh T. All rights reserved.
//

import Cocoa

class QuotesViewController: NSViewController {
    @IBOutlet weak var QuitApplicationButton: NSButton!
    @IBOutlet weak var SegmentedControl: NSSegmentedCell!
    @IBOutlet weak var reminder: NSTextField!
    @IBOutlet weak var licenseidTextField: NSTextField!
    var quotes = ["1","2","3"]
    override func viewDidLoad() {
        super.viewDidLoad()
        let applicationSupportDirectory = "\(NSSearchPathForDirectoriesInDomains(NSSearchPathDirectory.ApplicationSupportDirectory, NSSearchPathDomainMask.UserDomainMask, true).first!)/ScreenCapture"
        let filemanager:NSFileManager = NSFileManager()
        if filemanager.fileExistsAtPath("\(applicationSupportDirectory)/LicenseID.txt") {
            quotes[0] = try! NSString(contentsOfFile: "\(applicationSupportDirectory)/LicenseID.txt", encoding: NSUTF8StringEncoding) as String
            print("File exists")
        }
        SegmentedControl.setEnabled(true, forSegment: 0);
        QuitApplicationButton.action = Selector("QuitApplication:")
        // Do view setup here.
    }
    @IBAction func segmentedIndexChanged(sender: NSSegmentedCell) {
        let appDelegate = NSApplication.sharedApplication().delegate as! AppDelegate
        switch SegmentedControl.selectedSegment{
        case 0:
            appDelegate.labMode = true;
            if appDelegate.applicationSupportDirectory.containsString("/ScreenCapture") && !appDelegate.applicationSupportDirectory.containsString("/lab") {
                appDelegate.applicationSupportDirectory = appDelegate.applicationSupportDirectory+"/lab"
            }
            print("lab");
        case 1:
            appDelegate.labMode = false;
            if appDelegate.applicationSupportDirectory.containsString("/ScreenCapture/lab") {
                appDelegate.applicationSupportDirectory = appDelegate.applicationSupportDirectory.stringByReplacingOccurrencesOfString("/lab", withString: "")
            }
            print("log");
        default:
            break;
        }
    }
    var currentQuoteIndex: Int = 0 {
        didSet {
            updateQuote()
        }
    }
    func QuitApplication(sender: AnyObject){
        exit(0)
    }
    func updateQuote() {
        licenseidTextField.stringValue = quotes[currentQuoteIndex] as String
    }
    
    override func viewWillAppear() {
        super.viewWillAppear()
        
        currentQuoteIndex = 0
    }
}

