# import RPi.GPIO as GPIO

# GPIO.setmode(GPIO.BCM)
# led_pins = {1: 17, 2: 27, 3: 22}
# led_states ={1: False, 2: False, 3: False}


# def setup_gpio():
# 	for pin in led_pins.values():
# 		GPIO.setup(pin, GPIO.OUT)
# 		GPIO.setup(pin, GPIO.LOW)
		
# def toggle_led(led_id):
# 	current_state = led_states[led_id]
# 	new_state = not current_state
# 	led_states[led_id] = new_state
# 	GPIO.output(led_pins[led_id], GPIO.HIGH if new_state else GPIO.LOW)
	
	
# def cleanup():
# 	GPIO.cleanup()
