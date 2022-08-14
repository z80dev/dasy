(import rich [print inspect]
        boa.contract [VyperContract]
        hy
        dasy)

(defn get-src [path]
  (with [f (open path "r")]
    (.read f)))

(let [src (get-src "noret.dasy")
      read-src (.read hy src)
      parsed-src (.parse_src dasy src)
      body (. parsed-src body)
      f-def (get body 3)
      ret (get (. f-def body) 0)
      val (. ret value)
      ]
  (inspect val)
  )

#_(let [src (with [f (open "hello_world.dasy" "r")]
            (.read f))
      compilation_data (.compile dasy src)
      contract (VyperContract compilation_data)]
  (print f"calling (.multipleRets contract 10 20): {(.multipleRets contract 10 20)}")
  (print f"calling (.foo contract 10): {(.foo contract 10 )}")
(print f"calling (.setBase contract 10): {(.setBase contract 10 )}")
(print f"calling (.addToBase contract 10): {(.addToBase contract 10 )}")
(print f"calling (.base contract): {(.base contract )}")
  )
(let [src (with [f (open "noret.dasy" "r")]
            (.read f))
      compilation_data (.compile dasy src)
      contract (VyperContract compilation_data)]
    (print f"calling (.foo contract ): {(.foo contract )}")
    (print f"calling (.base contract) : {(.base contract)}")
  )
