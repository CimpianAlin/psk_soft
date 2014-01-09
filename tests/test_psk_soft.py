#!/usr/bin/env python
import unittest
import ossie.utils.testing
import os
from omniORB import any
import time

from ossie.utils import sb
from ossie.utils.sb import domainless
import struct
import cmath

import matplotlib.pyplot
                 

def toCx(input):
    output =[]
    for i in xrange(len(input)/2):
        output.append(complex(input[2*i], input[2*i+1]))
    return output 

class ComponentTests(ossie.utils.testing.ScaComponentTestCase):
    """Test for all component implementations in psk_soft"""

    def setUp(self):
        """Set up the unit test - this is run before every method that starts with test
        """
        ossie.utils.testing.ScaComponentTestCase.setUp(self)
        self.src = sb.DataSource()
        self.sink = sb.DataSink()
        
        #setup my components
        self.setupComponent()
        
        self.comp.start()
        self.src.start()
        self.sink.start()
        
        #do the connections
        self.src.connect(self.comp)        
        self.comp.connect(self.sink)
        
    def tearDown(self):
        """Finish the unit test - this is run after every method that starts with test
        """
        self.comp.stop()
        #######################################################################
        # Simulate regular component shutdown
        self.src.stop()
        self.sink.stop()      
        self.comp.releaseObject()
        ossie.utils.testing.ScaComponentTestCase.tearDown(self)

    def testCase(self):
        #f = file('/home/bsg/qpsk.dat','r')
        f = file('/home/bsg/out2','r')
        s = f.read()
        data = list(struct.unpack('%sf' %(len(s)/4),s))

        print "got %s data samples" %len(data)

        self.comp.samplesPerBaud=8
        print self.comp.samplesPerBaud   
        self.comp.numAvg=100   
        out = self.main(data,100)
        print len(out)
         
        #         matplotlib.pyplot.plot(out[::2], out[1::2],'o')
        #         matplotlib.pyplot.show()
        
        startSample=0
        endSample=20
        resampleFactor=1
        startIndex=0
        finalIndex=2000
        x = out[2*startIndex:finalIndex:resampleFactor*2]
        y = out[2*startIndex+1:finalIndex:resampleFactor*2]
        cx = [complex(i,j) for i,j in zip(x,y)]
        
        matplotlib.pyplot.plot(x, y,'o')
        matplotlib.pyplot.show()
        fourth = [pow(z,4) for z in cx]
        matplotlib.pyplot.plot(range(len(fourth)),[cmath.phase(z) for z in fourth] ,'o')
        matplotlib.pyplot.show()
        avgPhase = sum([cmath.phase(z) for z in fourth])/len(fourth)

        matplotlib.pyplot.plot([z.real for z in fourth],[z.imag for z in fourth] ,'o')
        matplotlib.pyplot.show()


#        for startIndex in xrange(10):
        if False:
            startIndex=5
            print startIndex
            resampleFactor = 8
            finalIndex = 251*resampleFactor
            x = data[2*startIndex:finalIndex:resampleFactor*2]
            y = data[2*startIndex+1:finalIndex:resampleFactor*2]
            #print x
            #print y
            #print data[:10]
            matplotlib.pyplot.plot(x,y,'o')
            matplotlib.pyplot.show()
            #matplotlib.pyplot.plot(xrange(len(x)),x,'o')
            #matplotlib.pyplot.show()


    def main(self,inData, sampleRate, complexData = True):
        """The main engine for all the test cases - configure the equation, push data, and get output
           As applicable
        """
        #data processing is asynchronos - so wait until the data is all processed
        count=0
        self.src.push(inData,
                      complexData = complexData, 
                      sampleRate=sampleRate)
        out=[]
        while True:
            newOut = self.sink.getData()
            if newOut:
                out.extend(newOut)
                count=0
            elif count==100:
                break
            time.sleep(.01)
            count+=1
        return out

    def setupComponent(self):
        #######################################################################
        # Launch the component with the default execparams
        execparams = self.getPropertySet(kinds=("execparam",), modes=("readwrite", "writeonly"), includeNil=False)
        execparams = dict([(x.id, any.from_any(x.value)) for x in execparams])
        self.launch(execparams)
        
        #######################################################################
        # Verify the basic state of the component
        self.assertNotEqual(self.comp, None)
        self.assertEqual(self.comp.ref._non_existent(), False)
        self.assertEqual(self.comp.ref._is_a("IDL:CF/Resource:1.0"), True)
        
        #######################################################################
        # Validate that query returns all expected parameters
        # Query of '[]' should return the following set of properties
        expectedProps = []
        expectedProps.extend(self.getPropertySet(kinds=("configure", "execparam"), modes=("readwrite", "readonly"), includeNil=True))
        expectedProps.extend(self.getPropertySet(kinds=("allocate",), action="external", includeNil=True))
        props = self.comp.query([])
        props = dict((x.id, any.from_any(x.value)) for x in props)
        # Query may return more than expected, but not less
        for expectedProp in expectedProps:
            self.assertEquals(props.has_key(expectedProp.id), True)
        
        #######################################################################
        # Verify that all expected ports are available
        for port in self.scd.get_componentfeatures().get_ports().get_uses():
            port_obj = self.comp.getPort(str(port.get_usesname()))
            self.assertNotEqual(port_obj, None)
            self.assertEqual(port_obj._non_existent(), False)
            self.assertEqual(port_obj._is_a("IDL:CF/Port:1.0"),  True)
            
        for port in self.scd.get_componentfeatures().get_ports().get_provides():
            port_obj = self.comp.getPort(str(port.get_providesname()))
            self.assertNotEqual(port_obj, None)
            self.assertEqual(port_obj._non_existent(), False)
            self.assertEqual(port_obj._is_a(port.get_repid()),  True)
            
        
    # TODO Add additional tests here
    #
    # See:
    #   ossie.utils.bulkio.bulkio_helpers,
    #   ossie.utils.bluefile.bluefile_helpers
    # for modules that will assist with testing components with BULKIO ports
    
if __name__ == "__main__":
    ossie.utils.testing.main("../psk_soft.spd.xml") # By default tests all implementations
