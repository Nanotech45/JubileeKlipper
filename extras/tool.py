import logging

class Tool:
    def __init__(self, config):        
        self.config  = config
        self.printer = config.get_printer()       
        self.name    = config.get_name().split()[1]
        self.gcode   = self.printer.lookup_object('gcode') 
        gcode_macro = self.printer.load_object(config, 'gcode_macro')
        self.dock    = self.printer.load_object(config, 'dock')
        #read the config..     
        self.parking_location = [ float(i) for i in config.get('parking_location').split(',')]
        self.zone_location    = [ float(i) for i in config.get('zone_location').split(',')]
        self.offset           = [ float(i) for i in config.get('offset').split(',')]
        #read the temmplates for the tool
        if config.get('unlock_gcode', None) is not None:
            self.tool_lock  =  gcode_macro.load_template(config, 'lock_gcode',None)
        else:
            self.tool_lock  = self.dock.tool_lock
        if config.get('unlock_gcode', None) is not None:
            self.tool_unlock  =  gcode_macro.load_template(config, 'unlock_gcode',None)
        else:
            self.tool_unlock  = self.dock.tool_unlock
        self.pre_zone  =  gcode_macro.load_template(config, 'pre_zone_gcode','')
        self.post_zone =  gcode_macro.load_template(config, 'post_zone_gcode', '')
        self.pre_park  =  gcode_macro.load_template(config, 'pre_park_gcode', '')
        self.post_park =  gcode_macro.load_template(config, 'post_park_gcode', '')
        self.gcode.register_mux_command(
            "BETA_TOOL_PICKUP", "TOOL", self.name,
            self.cmd_TOOL_PICKUP,
            desc=self.cmd_TOOL_PICKUP_help)                       
  
    cmd_TOOL_PICKUP_help= "Pick up a tool from the dock"
    def cmd_TOOL_PICKUP(self, gcmd):
         if self.dock.tool_present:
             self.dock.cmd_TOOL_DROPOFF(gcmd)
         #dropoff the tool if we have one.
         self.dock.cmd_TOOL_DROPOFF(gcmd)
         self._exec(self.pre_zone)
         #move to the tool pickup zone
         self.dock.move(self.zone_location, self.dock.travel_speed, gcmd)
         #move to the parking zone.
         self.dock.move(self.parking_location, self.dock.parking_speed, gcmd)
         self._exec(self.tool_lock)
         #move back to the pickup zone
         self.dock.move(self.zone_location, self.dock.travel_speed, gcmd)
         #apply the users offset
         self.dock.set_gcode_offset(self.offset)
         self._exec(self.post_zone)
         #Save the location of the tool so dropoff knows what to do later.
         self.dock.parking_location = self.parking_location
         self.dock.zone_location    = self.zone_location
         self.dock.tool_offset      = self.offset
         self.dock.tool_present     = True
         #move back to origin?
         gcmd.respond_info('prior state:"%s"'
            % (self.dock.tool_present,))

    def _exec(self, script):
        try:
            self.gcode.run_script_from_command(script.render())
        except Exception:
            logging.exception("Script running error")

def load_config_prefix(config):
    return Tool(config)