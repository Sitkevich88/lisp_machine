(setq a 0) ;вывод нечетных чисел от 0 до 20
(print (loop
   (if
        ( = (mod a 2) 1)
        (print a)
   )
   (setq a (+ a 1))
   (if (> a 20) (return "Конец цикла"))
))