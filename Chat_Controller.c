// #include <stdio.h>
// #include "pico/stdlib.h"
// #include "hardware/pwm.h"

// #define A_HIGH 16
// #define A_LOW  17
// #define B_HIGH 18
// #define B_LOW  19
// #define C_HIGH 20
// #define C_LOW  21

// // Store PWM slice/channel for each high pin
// uint slice_a, slice_b, slice_c;
// uint chan_a, chan_b, chan_c;

// // Duty cycle (0–65535)
// uint16_t duty_level = 20000; // start ~30%

// void pwm_init_pin(uint pin, uint16_t duty) {
//     gpio_set_function(pin, GPIO_FUNC_PWM);
//     uint slice = pwm_gpio_to_slice_num(pin);
//     uint chan  = pwm_gpio_to_channel(pin);
//     pwm_set_wrap(slice, 65535); // 16-bit resolution
//     pwm_set_chan_level(slice, chan, duty);
//     pwm_set_enabled(slice, true);
// }

// void set_duty(uint16_t duty) {
//     duty_level = duty;
//     pwm_set_chan_level(slice_a, chan_a, duty);
//     pwm_set_chan_level(slice_b, chan_b, duty);
//     pwm_set_chan_level(slice_c, chan_c, duty);
// }

// void all_off() {
//     pwm_set_chan_level(slice_a, chan_a, 0);
//     pwm_set_chan_level(slice_b, chan_b, 0);
//     pwm_set_chan_level(slice_c, chan_c, 0);

//     gpio_put(A_LOW, 0);
//     gpio_put(B_LOW, 0);
//     gpio_put(C_LOW, 0);
// }

// void activate_step(char step) {
//     all_off();

//     switch (step) {
//         case 'A': case 'a':
//             pwm_set_chan_level(slice_a, chan_a, duty_level);
//             gpio_put(B_LOW, 1);
//             printf("Step A: A_high PWM, B_low ON\n");
//             break;

//         case 'B': case 'b':
//             pwm_set_chan_level(slice_b, chan_b, duty_level);
//             gpio_put(C_LOW, 1);
//             printf("Step B: B_high PWM, C_low ON\n");
//             break;

//         case 'C': case 'c':
//             pwm_set_chan_level(slice_c, chan_c, duty_level);
//             gpio_put(A_LOW, 1);
//             printf("Step C: C_high PWM, A_low ON\n");
//             break;

//         default:
//             printf("Invalid input. Use A, B, or C.\n");
//             break;
//     }
// }

// int main() {
//     stdio_init_all();

//     // Init low side pins
//     gpio_init(A_LOW); gpio_set_dir(A_LOW, GPIO_OUT);
//     gpio_init(B_LOW); gpio_set_dir(B_LOW, GPIO_OUT);
//     gpio_init(C_LOW); gpio_set_dir(C_LOW, GPIO_OUT);

//     // Init PWM high side pins
//     pwm_init_pin(A_HIGH, duty_level);
//     pwm_init_pin(B_HIGH, duty_level);
//     pwm_init_pin(C_HIGH, duty_level);

//     // Save slice/channel mappings
//     slice_a = pwm_gpio_to_slice_num(A_HIGH);
//     chan_a  = pwm_gpio_to_channel(A_HIGH);
//     slice_b = pwm_gpio_to_slice_num(B_HIGH);
//     chan_b  = pwm_gpio_to_channel(B_HIGH);
//     slice_c = pwm_gpio_to_slice_num(C_HIGH);
//     chan_c  = pwm_gpio_to_channel(C_HIGH);

//     all_off();

//     printf("BLDC PWM Control Ready.\n");
//     printf("Type A/B/C for commutation step, 1–9 to adjust duty.\n");

//     while (true) {
//         int c = getchar_timeout_us(0);
//         if (c == PICO_ERROR_TIMEOUT) continue;

//         if (c >= '1' && c <= '9') {
//             uint16_t new_duty = (c - '0') * 65535 / 10; // 10%–90%
//             set_duty(new_duty);
//             printf("Duty set to %d%%\n", (c - '0') * 10);
//         } else {
//             activate_step((char)c);
//         }
//     }
// }
