import python
import semmle.python.dataflow.TaintTracking as TaintTracking

class SystemCall extends TaintTracking::Configuration {
  SystemCall() { this = "SystemCall"; }

  override predicate isSource(DataFlow::Node source) {
    exists(Call c | 
      c = source.asExpr() and
      c.getCalled().(Name).getId() = "input"
    )
  }

  override predicate isSink(DataFlow::Node sink) {
    exists(Call c | 
      c = sink.asExpr() and
      c.getCalled().(Attribute).getName() = "system" and
      c.getCalled().(Attribute).getScope().getEnclosingModule().getName() = "os"
    )
  }
}

from SystemCall call, DataFlow::Node source, DataFlow::Node sink
where call.hasFlow(source, sink)
select sink, "This call to os.system() potentially includes user input from: " + source + "."
