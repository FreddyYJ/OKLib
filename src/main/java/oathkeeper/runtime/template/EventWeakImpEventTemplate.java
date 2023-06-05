package oathkeeper.runtime.template;

import oathkeeper.runtime.OKHelper;
import oathkeeper.runtime.event.OpTriggerEvent;
import oathkeeper.runtime.event.SemanticEvent;
import oathkeeper.runtime.event.StateUpdateEvent;
import oathkeeper.runtime.invariant.Context;
import oathkeeper.runtime.invariant.Invariant;

import java.util.*;

public class EventWeakImpEventTemplate extends Template {
    public String getTemplateName() {
        return "EventWeakImpEventTemplate";
    }

    public int getOperatorSize() {
        return 2;
    }

    public Invariant genInv(Context context) {
        if(context.left instanceof OpTriggerEvent && context.right instanceof OpTriggerEvent)
            return new Invariant(new OpWeakImpOpTemplate(), context);
        else
            return null;
    }
    
    /**
     * p -> q: true
     * q -> p: true
     * q -> q: true
     * p -> p: false
     */
    public class InferScanner extends Template.InferScanner {
        Map<SemanticEvent, Map<SemanticEvent, Integer>> counterMap = new HashMap<>();
        Map<SemanticEvent, Map<SemanticEvent, Integer>> newCounterMap = new HashMap<>();
        Map<SemanticEvent, Integer> occurance = new HashMap<>();

        public void prescan(Set<SemanticEvent> eventSet) {
            for (SemanticEvent event : eventSet) {
                occurance.put(event, 0);
            }
            for (SemanticEvent event : eventSet) {
                counterMap.put(event, new HashMap<>());
            }

            for (SemanticEvent event : eventSet) {
                for (SemanticEvent event1 : eventSet) {
                    if (!event.equals(event1)) {
                        counterMap.get(event).put(event1, 0);
                        counterMap.get(event1).put(event, 0);
                    }
                }
            }
        }

        // structure look like
        // counterMap --------> 1 ---------> 2
        // 3
        // ...
        // 2 ---------> 1
        // 3
        // ...
        // 3 ---------->...
        public void scan(SemanticEvent event) {
            // appear before, so we update all counters
            // phase 1:
            Integer occ = occurance.get(event);
            occurance.put(event, occ + 1);
            if (occurance.get(event) >= 1) {
                for (Map.Entry<SemanticEvent, Integer> entry : counterMap.get(event).entrySet()) {
                    if (entry.getValue() <= 0) { // p -> p
                        entry.setValue(entry.getValue() - 1);
                    } else {
                        entry.setValue(0);
                    }
                }
            }
            // for (Map.Entry<SemanticEvent, Integer> entry :
            // counterMap.get(event).entrySet()) {
            // //if (entry.getValue() >= 0)
            // entry.setValue(entry.getValue() + 1);
            // }

            // phase 2:
            for (SemanticEvent event1 : counterMap.keySet()) {
                if (event.equals(event1))
                    continue;

                Integer val = counterMap.get(event1).get(event);
                if (val >= 0)
                    counterMap.get(event1).put(event, val + 1); // p -> q is valid when val > 0
            }
        }

        // check the after scan state, and judge
        public List<Invariant> postscan() {
            List<Invariant> lst = new ArrayList<>();
            for (Map.Entry<SemanticEvent, Map<SemanticEvent, Integer>> entry : counterMap.entrySet()) {
                for (Map.Entry<SemanticEvent, Integer> subEntry : entry.getValue().entrySet()) {
                    if (subEntry.getValue() > 0) {
                        Invariant inv = genInv(new Context(
                                entry.getKey(),
                                subEntry.getKey()));
                        if (inv != null)
                            lst.add(inv);
                    }
                }
            }

            return lst;
        }
    }

    public class VerifyScanner extends Template.VerifyScanner
    {
        Context context;
        State state;
        class State{
            boolean ifHold = true;
            boolean ifActivated = false;
            int counter = 0;
        }

        public void prescan() {
            state = new State();
        }

        public boolean scan(SemanticEvent event) {
            if (event.equals(context.left)) {
                state.counter++;
                state.ifActivated = true;
                OKHelper.debug("counter++");
            } else if (event.equals(context.right) && state.counter > 0) {
                state.counter--;
                OKHelper.debug("counter--");
            }

            return true;
        }

        public void postscan() {
            if (state.counter != 0)
            {
                state.ifHold = false;
                OKHelper.debug("counter:"+state.counter);
            }
        }

        public Invariant.InvState getRetVal() {
            if(!state.ifHold)
                return Invariant.InvState.FAIL;
            else{
                if(state.ifActivated)
                    return Invariant.InvState.PASS;
                else return Invariant.InvState.INACTIVE;
            }
        }
        public VerifyScanner(Context context) {
            this.context = context;
        }
    }

    public Template.InferScanner getInferScanner()
    {
        return new InferScanner();
    }
    public Template.VerifyScanner getVerifyScanner(Context context)
    {
        return new VerifyScanner(context);
    }

    public Template invert()
    {
        throw new RuntimeException("IMPOSSIBLE");
    }
}
