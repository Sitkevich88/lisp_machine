( setq result 0 )

(loop for i from 0 to 999 do
	( if
         ( = ( mod i 3 ) 0 )
         ( setq result ( + result i ) )
         ( if
              ( = ( mod i 5 ) 0 )
              ( setq result ( + result i ) )
          )
    )
)

( print result )