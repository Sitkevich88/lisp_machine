( setq result 0 )

(setq i 0)
(loop
	( if
         ( = ( mod i 3 ) 0 )
         ( setq result ( + result i ) )
         ( if
              ( = ( mod i 5 ) 0 )
              ( setq result ( + result i ) )
          )
    )
    (setq i (+ i 1))
    (if (> i 999) (return))
)

( print result )