Jika processing_data.py ini terkena memory limit approach yang bisa di lakukan:
- ambil data di read csv dengan chunk
- filter per suplier / vendor
- filter bulan mungkin

intinya lakukan seperkecil mungkin

- setelah di menggunakan cara diatas lakukan write data per filter dan export ke system berupa csv

- kemudian lakukan read data ke setiap hasil export data tersebut, gabungkan per csv menjadi satu excel yang utuh.