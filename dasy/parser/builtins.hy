(import vyper.ast.nodes *
        .utils [next_nodeid])
(require
  hyrule.control [case])

(defn build-node [t #* args #** kw-args]
  (t :node-id (next_nodeid) :ast-type (. t __name__) #* args #** kw-args))

(defn parse-builtin [node]
  (case (str node)
        "+" (build-node Add  :-pretty "+" :-description "addition")
        "-" (build-node Sub :-pretty "-" :-description "subtraction")
        "*" (build-node Mult :-pretty "*" :-description "multiplication")
        "**" (build-node Pow :-pretty "**" :-description "exponentiation")
        "/" (build-node Div :-pretty "/" :-description "division")
        "<" (build-node Lt :-pretty "<" :-description "less than")
        ">" (build-node Gt :-pretty ">" :-description "greater than")
        "<=" (build-node LtE :-pretty "<=" :-description "less than equal")
        ">=" (build-node GtE :-pretty ">=" :-description "greater than equal")
        "==" (build-node Eq :-pretty "==" :-description "equal")
        "!=" (build-node NotEq :-pretty "!=" :-description "not equal")
        "not" (build-node Not :-pretty "not" :-description "negation")
        "and" (build-node And :-pretty "and" :-description "boolean and")
        "or" (build-node Or :-pretty "or" :-description "boolean or")))
