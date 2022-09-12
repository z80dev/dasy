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
        "%" (build-node Mod :-pretty "%" :-description "modulus")
        "^" (build-node BitXor :-pretty "^" :-description "bitwise xor")
        "|" (build-node BitOr :-pretty "|" :-description "bitwise or")
        "&" (build-node BitAnd :-pretty "&" :-description "bitwise and")
        "~" (build-node Invert :-pretty "~" :-description "bitwise not")
        "/" (build-node Div :-pretty "/" :-description "division")
        "<" (build-node Lt :-pretty "<" :-description "less than")
        ">" (build-node Gt :-pretty ">" :-description "greater than")
        "<=" (build-node LtE :-pretty "<=" :-description "less than equal")
        ">=" (build-node GtE :-pretty ">=" :-description "greater than equal")
        "==" (build-node Eq :-pretty "==" :-description "equal")
        "!=" (build-node NotEq :-pretty "!=" :-description "not equal")
        "in" (build-node In :-pretty "in" :-description "membership")
        "notin" (build-node NotIn :-pretty "not in" :-description "exclusion")
        "not" (build-node Not :-pretty "not" :-description "negation")
        "and" (build-node And :-pretty "and" :-description "boolean and")
        "or" (build-node Or :-pretty "or" :-description "boolean or")))
