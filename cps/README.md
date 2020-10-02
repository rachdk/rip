Need to integrate python code with matching to be able to write things like:'

```
(rule ((:IN (expanded (integrate (integral (+ ?tl ?t2) ?var))) :VAR ?starter))
    (rlet ((?integral (integral (+ ?t1 ?t2) ?var))
           (?problem (integrate (integral (+ ?tl ?t2) ?var))))
        (rlet ((?op-instance (integral-of-sum ?integral))) 
            (rassert! (operator-instance ?op-instance)  :OP-INSTANCE-DEFINITION)
            (rassert! (suggest-for ?problem ?op-instance)   (:INTOPEXPANDER ?starter))
            (rule ((:IN (expanded (try ?op-instance)) :VAR ?trying))
                (rlet ((?goal0 (integrate (integral (:EVAL (simplify ?t1)) ?var)))
                       (?goall (integrate (integral (:EVAL (simplify ?t2)) ?var))))
                       (queue-problem ?goal0 ?problem) (queue-problem ?goall ?problem)
            (rassert! (and-subgoals (try ?op-instance)
                      (?goal0 ?goall)) (:INTEGRAL-OF-SUM-DEF ?trying))
            (rule ((:IN (solution-of ?goal0 ?intl) :VAR ?result0) 
                   (:IN (solution-of ?goall ?int2) :VAR ?resultl))
                (rlet ((?solution (:EVAL (simplify '(+ ,?intl ,?in2))))) 
                   (rassert! (solution-of ?problem ?solution)
                    (:INTEGRAL-OF-SUM (operator-instance ?op-instance) ?result0 ?resultl)))))))))
```

Need to separate JTMS from JTRE

JTMS is the structure of nodes connected to each other
JTRE is the rule engine