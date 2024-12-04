//
//  Bash.swift
//  ScreenCapture
//
//  Created by kin on 8/4/19.
//  Copyright © 2019 Vuong, Thanh T. All rights reserved.
//

import Foundation

protocol CommandExecuting {
    func execute(commandName: String) -> String?
    func execute(commandName: String, arguments: [String]) -> String?
}

final class Bash: CommandExecuting {
    
    // MARK: - CommandExecuting
    
    func execute(commandName: String) -> String? {
        return exec(commandName, arguments: [])
    }
    
    func execute(commandName: String, arguments: [String]) -> String? {
        //guard var bashCommand = exec("/bin/bash", arguments: ["-l", "-c", "\(commandName)"]) else { return "\(commandName) not found" }
        guard var bashCommand = exec("/usr/bin/which", arguments: ["\(commandName)"]) else { return "\(commandName) not found" }
        bashCommand = bashCommand.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceAndNewlineCharacterSet())
        return exec(bashCommand, arguments: arguments)
        //return exec(commandName, arguments: arguments)
    }
    
    // MARK: Private
    
    private func exec(command: String, arguments: [String] = []) -> String? {
        let task = NSTask()
        task.launchPath = command
        task.arguments = arguments
        
        let pipe = NSPipe()
        task.standardOutput = pipe
        task.launch()
        
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        let output = String(data: data, encoding: NSUTF8StringEncoding)
        return output!
    }
}