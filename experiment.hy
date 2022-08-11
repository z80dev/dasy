(import rich [print inspect]
        boa.contract [VyperContract]
        hy
        dasy)

(defn get-src [path]
  (with [f (open path "r")]
    (.read f)))

(let [src (get-src "hello_world.dasy")]
  (inspect (.read hy src))
  (inspect (.parse_src dasy src)))

(let [src (with [f (open "hello_world.dasy" "r")]
            (.read f))
      compilation_data (.compile dasy src)
      contract (VyperContract compilation_data)]
  (print f"calling (.multipleRets contract 10 20): {(.multipleRets contract 10 20)}")
  )
