package oathkeeper.runtime.template;

import oathkeeper.runtime.event.OpTriggerEvent;
import oathkeeper.runtime.event.SemanticEvent;
import oathkeeper.runtime.event.StateUpdateEvent;
import oathkeeper.runtime.invariant.Context;
import oathkeeper.runtime.invariant.Invariant;

public class StateChangeWeakImpStateChangeTemplate extends EventWeakImpEventTemplate {
    // semantics: for all op p, there should be subsequent op q invoked
    // p⇒q
    // allow q => q, q => p
    // but not allow p => p

    @Override
    public String getTemplateName() {
        return "StateChangeWeakImpStateChangeTemplate";
    }

    @Override
    public boolean checkLeftEventClass(SemanticEvent event)
    {
        return event instanceof StateUpdateEvent;
    }

    @Override
    public boolean checkRightEventClass(SemanticEvent event)
    {
        return event instanceof StateUpdateEvent;
    }

    @Override
    public Invariant genInv(Context context) {
        return new Invariant(new StateChangeWeakImpStateChangeTemplate(), context);
    }

}
