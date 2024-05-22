Возникла необходимость автономного инструмента раздачи текущего беклога заданий сотрудникам. 

Условия:

- данные для заданий содержатся в excel-таблицах;
- названия excel-таблиц формата "id категории" + "порядковый номер фрагмента" (если в рамках одной категории несколько файлов): //435261.xlsx; 238901_1.xlsx; 238901_2.xlsx; ...//
- в рамках одной категории пользователь может получить только 1 файл;
- выдача должна быть доступна только пользователям из списка.

Было принято решение написать несложного бота, который будет по запросу выдавать пользователю файл. Все необходимые данные будут храниться на Я.диске: 

- папка "res" -- технические файлы: allowed_users.txt (уайтлист пользователей), sent_files_log.txt (логи выданных файлов в привзяке к пользователям);
- папка "working_folder" -- беклог файлов;
- папка "given_folder" -- выданые в работу файлы (сюда после выдачи польхователю попадает файл из папки working_folder).

Функции бота: 
- /get_file -- выдает файл с данными для задания;
- /backlog -- показывает доступное количество файлов (общее количество + количество уникальных категорий).

----------------------------
The need has arisen for an autonomous tool to distribute the current task backlog to employees.

Conditions:

- the data for tasks is contained in Excel tables;
- the names of the Excel tables follow the format "category id" + "fragment sequence number" (if there are multiple files within one category): //435261.xlsx; 238901_1.xlsx; 238901_2.xlsx; ...//
- within one category, a user can receive only one file;
- distribution should be available only to users from a specified list.

It was decided to create a simple bot that will provide users with a file upon request. All necessary data will be stored on Yandex Disk:

- folder "res" -- technical files: //allowed_users.txt (whitelist of users), sent_files_log.txt (log of files issued linked to users)//;
- folder "working_folder" -- backlog of files;
- folder "given_folder" -- files issued for work (after being issued to a user, the file from the working_folder moves here).

Bot functions:

- /get_file -- provides a file with task data;
- /backlog -- shows the available number of files (total number + number of unique categories).
