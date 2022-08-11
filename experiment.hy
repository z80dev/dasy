(import rich [print]
        boa.contract [VyperContract]
        dasy)

(let [src (with [f (open "hello_world.dasy" "r")]
            (.read f))
      compilation_data (.compile dasy src)
      contract (VyperContract compilation_data)]
  (print f"calling (.addUints contract 10 20): {(.addUints contract 10 20)}")
  (print f"calling (.subUints contract 10 20): {(.subUints contract 100 20)}"))
