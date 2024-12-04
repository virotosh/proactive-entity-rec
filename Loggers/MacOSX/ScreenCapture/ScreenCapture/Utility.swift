//
//  Utility.swift
//  ScreenCapture
//
//  Created by kin on 8/4/19.
//  Copyright © 2019 Vuong, Thanh T. All rights reserved.
//

import Foundation

final class Utility {
    
    // Genrate mac address from the computer
    func macSerialNumber() -> String? {
        // Get the platform expert
        let platformExpert: io_service_t = IOServiceGetMatchingService(kIOMasterPortDefault, IOServiceMatching("IOPlatformExpertDevice"));
        
        // Get the serial number as a CFString ( actually as Unmanaged<AnyObject>! )
        let serialNumberAsCFString = IORegistryEntryCreateCFProperty(platformExpert, kIOPlatformSerialNumberKey, kCFAllocatorDefault, 0);
        
        // Release the platform expert (we're responsible)
        IOObjectRelease(platformExpert);
        
        // Take the unretained value of the unmanaged-any-object
        // and pass it back as a String or, if it fails, an empty string
        return (serialNumberAsCFString.takeUnretainedValue() as? String) ?? ""
    }
    
    // Convert string to dictionary format
    func convertStringToDictionary(text: String) -> [String:AnyObject]? {
        if let data = text.dataUsingEncoding(NSUTF8StringEncoding) {
            do {
                return try NSJSONSerialization.JSONObjectWithData(data, options: []) as? [String:AnyObject]
            } catch let error as NSError {
                //print(error)
            }
        }
        return nil
    }
    
    // Compare character count of the strings.
    func length(value1: String, value2: String) -> Bool {
        return value1.characters.count < value2.characters.count
    }
    
    // Count substrings in string
    func count(s: String, sub_s: String) -> Int {
        let tok =  s.componentsSeparatedByString(sub_s)
        if tok.count > 1 {
            return tok.count - 1
        }
        else{
            return 0
        }
    }
    
    func runPythonInBackground(path: String) -> Void {
        dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0)) {
            let bash: CommandExecuting = Bash()
            if let lsOutput = bash.execute("python", arguments:["\(path)/corpus_modified.py", "\(path)"]) { print(lsOutput) }
            
            if !path.containsString("lab"){
                let fileManager = NSFileManager.defaultManager()
                do {
                    if fileManager.fileExistsAtPath("\(path)/lab/original_corpus/corpus.mm") {
                        try fileManager.removeItemAtPath("\(path)/lab/original_corpus/corpus.mm")
                        try fileManager.removeItemAtPath("\(path)/lab/original_corpus/corpus.mm.index")
                        try fileManager.removeItemAtPath("\(path)/lab/original_corpus/dictionary.dict")
                    }
                    
                    try fileManager.moveItemAtPath("\(path)/corpus/corpus.mm", toPath: "\(path)/lab/original_corpus/corpus.mm")
                    
                    try fileManager.moveItemAtPath("\(path)/corpus/corpus.mm.index", toPath: "\(path)/lab/original_corpus/corpus.mm.index")
                    
                    try fileManager.moveItemAtPath("\(path)/corpus/dictionary.dict", toPath: "\(path)/lab/original_corpus/dictionary.dict")
                }
                catch let error as NSError {
                    print(error)
                }
                
                if let lsOutput = bash.execute("python", arguments:["\(path)/build_views_modified.py", "\(path)"]) { print(lsOutput) }
            }
            else
            {
                
            }
        }
        
    }
}