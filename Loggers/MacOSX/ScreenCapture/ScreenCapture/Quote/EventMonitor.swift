//
//  EventMonitor.swift
//  ScreenCapture
//
//  Created by kin on 1/4/17.
//  Copyright © 2017 Vuong, Thanh T. All rights reserved.
//

import Cocoa

public class EventMonitor: NSObject {
    private var monitor: AnyObject?
    private let mask: NSEventMask
    private let handler: NSEvent? -> ()
    
    public init(mask: NSEventMask, handler: NSEvent? -> ()) {
        self.mask = mask
        self.handler = handler
    }
    
    deinit {
        stop()
    }
    
    public func start() {
        monitor = NSEvent.addGlobalMonitorForEventsMatchingMask(mask, handler: handler)
    }
    
    public func stop() {
        if monitor != nil {
            NSEvent.removeMonitor(monitor!)
            monitor = nil
        }
    }
}
