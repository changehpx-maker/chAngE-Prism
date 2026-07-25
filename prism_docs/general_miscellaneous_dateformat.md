## Changing the date format in the Prism User Interface

The "PRISM\_DATE\_FORMAT" environment variable can be used to change the date and time display for in the Prism User Interfaces. Setting the variable can be done easily in the Prism User Settings, in the Prism Project Settings or in your OS environment settings.

The value of this variable is a string, which would be used in Python typically to format a date. This string can contain any combination of characters and predefined variables. A predefined variables starts with "%" followed by a character like "%d", which will evaluate to the number of the month. Here is a list of all available variables: [https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)

This is the default format used in Prism:

- "%d.%m.%y, %H:%M:%S" -> "31.03.22 14:50:12"

Some examples for possible values:

- "%Y-%m-%d, %H:%M%p" -> "2022-31-03, 2:50PM"
- "%B %d, %Y - %H:%M%p" -> "March 31, 2022 - 2:50PM"
- "abc %H:%M:%S %% %d/%m/%Y" -> "abc 14:50:12 % 31/03/2022"
![../../../_images/dateformat.jpg](https://prism-pipeline.com/docs/latest/_images/dateformat.jpg)