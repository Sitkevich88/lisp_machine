(setq a 10)
(loop
   (setq a (+ a 1))
   (print a)
   (when (> a 19) (return))
)