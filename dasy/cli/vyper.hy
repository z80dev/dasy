(import sys)
(import click)
(import dasy [compiler parser])
(import vyper.compiler [OUTPUT_FORMATS :as VYPER_OUTPUT_FORMATS])
(import dasy.parser.output [get_external_interface])


(setv format-help
"
Format to print, one or more of:

    bytecode (default) - Deployable bytecode
    bytecode_runtime   - Bytecode at runtime
    abi                - ABI in JSON format
    abi_python         - ABI in python format
    source_map         - Vyper source map
    method_identifiers - Dictionary of method signature to method identifier
    userdoc            - Natspec user documentation
    devdoc             - Natspec developer documentation
    combined_json      - All of the above format options combined as single JSON output
    layout             - Storage layout of a Vyper contract
    ast                - AST in JSON format
    external_interface - External (Dasy) interface of a contract, used for outside contract calls
    vyper_interface    - External (Vyper) interface of a contract, used for outside contract calls
    opcodes            - List of opcodes as a string
    opcodes_runtime    - List of runtime opcodes as a string
    ir                 - Intermediate representation in list format
    ir_json            - Intermediate representation in JSON format
    hex-ir             - Output IR and assembly constants in hex instead of decimal
    no-optimize        - Do not optimize (don't use this for production code)
")


(setv OUTPUT_FORMATS (VYPER_OUTPUT_FORMATS.copy))
(setv (get OUTPUT_FORMATS "vyper_interface") (get OUTPUT_FORMATS "external_interface"))
(setv (get OUTPUT_FORMATS "external_interface") get_external_interface)

(defmacro with-open [filename body]
  `(with [f (open ~filename "r")]
     ~@body))


(defn compile-contract [filename]
  (if filename
    (with-open filename
        (if (filename.endswith ".vy")
          (setv data (compiler.compilerData src :contract-name (get (split (filename.split "/") "." ) 0)))
          (setv data (compiler.compile src :name (get (filename.split ".")0)))))
    (do
      (for [line (sys.stdin)]
          (setv src (+ src line)))
          (setv data (compiler.compile src :name "StdIn")))))

(setv translate-map (dict
  [["abi_python" "abi"]
   ["json" "abi"]
   ["ast" "ast_dict"]
   ["ir_json" "ir_dict"]
   ["interface" "external_interface"]]))

(defn process-output [translate-map data format OUTPUT_FORMATS]
  (setv output-format (.get translate-map format format))
  (if (in output-format (keys OUTPUT_FORMATS))
    (print ((get OUTPUT_FORMATS output-format) data))
    (raise (click.ClickException
             (str "Unrecognized Output Format " format ". Must be one of " (keys OUTPUT_FORMATS))))))


(defn
  [click.command
   (click.option "-f" "--format" :help format-help :default "bytecode")]
  main [filename format]
  (process-output translate-map (compile-contract filename) format OUTPUT_FORMATS))



