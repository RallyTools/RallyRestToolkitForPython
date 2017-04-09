
import sys
import copy
from threading import Thread
import six
from six.moves import queue
Queue = queue.Queue

__version__ = (1, 3, 1)

#########################################################################################################

class CargoTruck:
    """
        A CargoTruck instance is charged with "filling" itself up with 
        boxes (sub-containers) where each box except the last one has max_items in it
        from the list of orders it must fulfill.  (The last box may have fewer than max_items...).
        Threads are used to obtain the items for the orders, where up to num_loaders
        number of threads can be used to "simultaneously" fulfill an individual order.
        An order (an URL) is retrieved and the data payload (JSON containing a list of "goods")
        is stuffed into a box.  The box has serial number (index associated with the order)
        such that it is stuffed into the Truck's storage container so that upon emptying
        the container, the items come out in the box serial number order.
    """

    def __init__(self, orders, num_loaders):
        self.orders      = orders
        self.num_loaders = num_loaders
        self.tank = {}

    def load(self, agent, method_name, timeout):
        """
            Given an agent (a clone of a requests.Session instance) and a method name for that 
            agent to execute,  start up num_threads threads to execute the method in parallel 
            on individual items in the self.orders list.  The results are put into a dict that
            is indexed from 1 .. num_threads with the value at each index a result of the 
            invocation on the agent of the method_name.
        """
        self.agent = agent
        self.tank  = {}
        threads    = []
        payload_queue = Queue(0)

        def pageGetter(agent, method_name, index, order, resq, timeout):
            activity = getattr(agent, method_name)
            try:
                result = activity(order, timeout=timeout)
            except:
                exc_name, exc_desc = sys.exc_info()[:2]
                notice = "||||||||||||||\nCargoTruck.load.pageGetter exception: %s, %s\n||||||||||||\n"
                #sys.stderr.write(notice % (exc_name, exc_desc))
                result = None
            resq.put((index, result))

        for ix, order in enumerate(self.orders):
            self.tank[ix+1] = None
            thread_safe_agent = copy.copy(self.agent)
            getter_args = (thread_safe_agent, method_name, ix+1, order, payload_queue, timeout)
            t = Thread(target=pageGetter, args=getter_args)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        if payload_queue.qsize() != len(self.orders):
            raise Exception("CargoTruck.load payload_queue size too short, only %d of %d expected items present" % \
                            (payload_queue.qsize(), len(self.orders)))

        while not payload_queue.empty():
            ix, results = payload_queue.get()
            #print("item: %d from payload_queue: |%s|" % (ix, results))
            self.tank[ix] = results
        shorted = [ix for ix in self.tank if self.tank[ix] == None]
        if shorted:
            filled = len(self.orders) - len(shorted)
            notice = "CargoTruck.load detected incomplete payload_queue, only %d of %d expected items present"
            raise Exception(notice % (filled, len(self.orders)))

        #payload_queue.task_done()  # apparently not needed or useful

    def dump(self):
        """
            To be called after a load has completed.  This method collects up the results that
            were put in the self.tank dict by iterating over the keys in key integer order and
            filling up a list with the results value for each dict key. This insures that the
            final single list returned is in the correct item order. 
        """
        payload = []
        indices = sorted([k for k in self.tank.keys()])
        for ix in indices:
            if not self.tank[ix]:  # no result for this index?
                raise Exception("CargoTruck.dump, no result at index %d for request: %s" % (ix, self.orders[ix]))
            else:
                payload.extend([self.tank[ix]])
        return payload 

