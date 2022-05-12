
// Add equals() to Array
// https://stackoverflow.com/a/14853974/1079688
//
// Warn if overriding existing method
if(Array.prototype.equals)
	console.warn("Overriding existing Array.prototype.equals.");

// attach the .equals method to Array's prototype to call it on any array
Array.prototype.equals = function (array) {
	// if the other array is a falsy value, return
	if (!array)
	    return false;
	
	// compare lengths - can save a lot of time 
	if (this.length != array.length)
	    return false;
	
	for (var i = 0, l=this.length; i < l; i++) {
	    // Check if we have nested arrays
	    if (this[i] instanceof Array && array[i] instanceof Array) {
	        // recurse into the nested arrays
	        if (!this[i].equals(array[i]))
	            return false;       
	    }           
	    else if (this[i] != array[i]) { 
	        // Warning - two different object instances will never be equal: {x:20} != {x:20}
	        return false;   
	    }           
	}       
	return true;
}

function numRange (start, end) {
	return new Array(end - start).fill().map((d, i) => i + start);
}	

function randTxt(len) {
	var text = "";
	var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
	
	for (var i = 0; i < len; i++)
	    text += possible.charAt(Math.floor(Math.random() * possible.length));
	
	return text;
}

// after https://bl.ocks.org/mbostock/7555321
function wrap0(text, width) {
	  text.each(function() {
	    var text = d3.select(this),
	        words = text.text().split(/\s+/).reverse(),
	        word,
	        line = [],
	        lineNumber = 0,
	        lineHeight = 1.1, // ems
	        y = text.attr("y"),
	        dy = parseFloat(text.attr("dy")),
	        tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
	    while (word = words.pop()) {
	      line.push(word);
	      tspan.text(line.join(" "));
	      if (tspan.node().getComputedTextLength() > width) {
	        line.pop();
	        tspan.text(line.join(" "));
	        line = [word];
	        tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
	      }
	    }
	  });
	}

function wrap(d3text, width) {
	var words = d3text.text().split(/\s+/).reverse(),
        word,
        line = [],
        lineNumber = 0,
        lineHeight = 1.1, // ems
        y = d3text.attr("y"),
        dy = '0em', // parseFloat(d3text.attr("dy")),
        tspan = d3text.append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
    while (word = words.pop()) {
      line.push(word);
      tspan.text(line.join(" "));
      if (tspan.node().getComputedTextLength() > width) {
        line.pop();
        tspan.text(line.join(" "));
        line = [word];
        tspan = d3text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
      }
    }
}

function make_editable(d, field) {
	// http://bl.ocks.org/GerHobbelt/2653660
	// console.log("make_editable", arguments);
	
	this
	    .on("mouseover", function() {
	        d3.select(this).style("fill", "red");
	    })
	    .on("mouseout", function() {
	        d3.select(this).style("fill", null);
	    })
	    .on("click", function(d) {
	        var p = this.parentNode;
	        // console.log(this, arguments);
			
	        // inject a HTML form to edit the content here...
			
	        // bug in the getBBox logic here, but don't know what I've done wrong here;
	        // anyhow, the coordinates are completely off & wrong. :-((
	        var xy = this.getBBox();
	        var p_xy = p.getBBox();
			
	        xy.x -= p_xy.x;
	        xy.y -= p_xy.y;
			
	        var el = d3.select(this);
	        var p_el = d3.select(p);
			
	        // var frm = p_el.append("foreignObject");
		var foid = "_makeEdit";

	        var frm = p_el.append("foreignObject")
		    .attr("id",foid);

	        var inp = frm
	            .attr("x", xy.x)
	            .attr("y", xy.y)
	            .attr("width", 300)
	            .attr("height", 25)
	            .append("xhtml:form")
	            .append("input")
	            .attr("value", function() {
	                // nasty spot to place this call, but here we are sure that the <input> tag is available
	                // and is handily pointed at by 'this':
	                this.focus();
					
	                return d[field];
	            })
	            .attr("style", "width: 294px;")
	            // make the form go away when you jump out (form looses focus) or hit ENTER:
	            .on("blur", function() {
	                // console.log("blur", this, arguments);
					
	                var txt = inp.node().value;
					
	                d[field] = txt;
	                el.text(function(d) { return d[field]; });
					
	                // Note to self: frm.remove() will remove the entire <g> group! Remember the D3 selection logic!
	                p_el.select("foreignObject").remove();
	            })
	            .on("keypress", function() {
	                // console.log("keypress", this, arguments);
					
	                // IE fix
	                if (!d3.event)
	                    d3.event = window.event;
					
	                var ev = d3.event;
					// RETURN (Tab=11 doesn't work?!) causes post
	                if (ev.keyCode == 13) {
	                    if (typeof(ev.cancelBubble) !== 'undefined') // IE
	                        ev.cancelBubble = true;
	                    if (ev.stopPropagation)
	                        ev.stopPropagation();
	                    ev.preventDefault();
						
	                    var txt = inp.node().value;
						
	                    d[field] = txt;
	                    el.text(function(d) { return d[field]; });
						
	                    // odd. Should work in Safari, but the debugger crashes on this instead.
	                    // Anyway, it SHOULD be here and it doesn't hurt otherwise.
	                    p_el.select("foreignObject").remove();
	                }
	            });
	    });
}	

function d3clog(lbl,d,i,node,thisDOM) {

	console.log('\n* '+lbl+" d: " + JSON.stringify(d),
				"\nIndex: " + JSON.stringify(i),
				"\nNode: " + JSON.stringify(node),
				"\nthis: " + JSON.stringify(thisDOM));
}
//////////////////////////////////

var MAX_ZOOM_IN = 2.0;
var MAX_ZOOM_OUT = 0.2;
var zoomStep = 0.2;
var actualZoomLevel = 1.0;
var MOVE_STEP = 100;
var zoomable_layer, zoom;

var width = 960;
var height = 1000;
var margin = {top: 10, right: 10, bottom: 30, left: 10}	

//SVG Coordinate space has x=0 and y=0 coordinates fall on the top left.
// Y coordinate growing from top to bottom. 

var menuLeft = 20;
var menuWOTop = 0;
var menuWidth = Math.round(width * 0.25);
var menuWOHgt = Math.round(height * 0.04);

var menuOtherLeft = Math.round(width * 0.7);
var menuOtherTop = 0; //  = Math.round(height * 0.3);
var menuOtherHgt = Math.round(height * 0.015);
var rectRndX = Math.round(menuWidth * 0.2);
var woRectRndY = Math.round(menuWOHgt * 0.5);
var otherRectRndY = Math.round(menuOtherHgt * 0.4);

var schedTop = 0;

// 2do: Shift scedule left for WOSgraphic
var schedLeft = Math.round(width * 0.3);

var schedWid = Math.round(width * 0.4);
var schedRight = schedLeft+schedWid;
var schedHgt = height;
// ASSUME divide schedule into 5 min increments
var schedMoveHgt = Math.round(schedHgt / 12.);
var schedRndX = Math.round(schedMoveHgt * 0.5);
var schedRndY = Math.round(schedWid * 0.5);
var schedLMargin = 0;
var schedOpacity = 0.5;
var menuSpacer = 5;

var circuitLeft = Math.round(width * 0.38);
var circuitWid = schedLeft + schedWid - circuitLeft; 
var circBorderWid = 4;

// bind data analogous to that from info to warmUp DOM
// NB: idx=0, nrep=0 because no real movement for warmUp, coolDown

var wuData = {"access": "", 
			  "measure": "WarmUp", 
			  "name": "WarmUp", 
			  "woRole": "WU",
			  "idx": 0,
			  "nrep": 0,
			  "annote": "(notes re: warm-up)"};

var wuSlot = {'schedIdx': 0,
			  'duration': [5,'m'],
			  'slotFiller': wuData};
			  
var cdData = {"access": "", 
			  "measure": "CoolDown", 
			  "name": "CoolDown", 
			  "woRole": "CD", 
			  "idx": 0,
			  "nrep": 0,
			  "annote": "(notes re: cooldown)"} ;
 
function fillColor(measureName) {
	var rgb;
	if (measureName in MeasureColor)
		rgb = MeasureColor[measureName];
	else
		rgb = MeasureColor['OPEN'];
	
	rgbStr = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
	return rgbStr}

function strokeColor(measureName) {
	var rgb;
	if (measureName in MeasureColor)
		rgb = MeasureColor[measureName];
	else
		rgb = MeasureColor['OPEN'];
	var strokeColor;
	if (rgb.equals([255,255,255])) {
		strokeColor = 'black';
	} else {
		strokeColor = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
	}
	return strokeColor}

// HACK: MeasureColor needs to be shared across drawWOS.html, drawMeso.js, views.py
var MeasureColor = {"Assault Bike": [255, 153, 51], 
					"Split Squat": [255,0,0],
					"TB Deadlift": [236,236,19], // [255,255,0],
					"Pull-Up": [164,194,244],
					"Push-Up": [153,204,0], // [182,215,168],
					"Turkish Get-Up" : [180,167,214],
					"OPEN": [230,230,230],
					'WarmUp': [255,255,255],
					'CoolDown': [255,255,255],
		                        "Hip CAR": [255, 102, 204]
		   };

var woFontSize = '12px' ;
var otherFontSize = '10px' ;
var schedFontSize = '14px' ;
var nrepFontSize = '24px' ; // 28;
var annoteFontSize= '12px' ;

var sketch = d3.select("#wosketch")
	.attr("width", width)
	.attr("height", height);

var schedGroup = sketch.append("g")
	.attr("class","schedGroup");

var schedGrid = schedGroup.append("g")
	.attr("class","schedGrid");

var schedBox = schedGrid.append("rect")
	.attr("x", schedLeft)
	.attr("y", schedTop)
	.attr("height", schedHgt)
	.attr("width", schedWid)
	.style("stroke","black")
	//.style("opacity",0.5)
	.style("fill","white");

var schedLines = schedGrid.selectAll('g')
	.data(numRange(1,12))
	.enter()
	.append("line")
	.attr("x1", schedLeft)
// NB: make grid lines at 5 min vs. 10 min move time
	.attr("y1", function(d,i) { return schedTop + d * schedMoveHgt; })
	.attr("x2", schedLeft + schedWid)
	.attr("y2", function(d,i) { return schedTop + d * schedMoveHgt; })
	.style("stroke","lightgrey");

// NB: need to place schedContent AFTER schedGrid!
var schedContent = schedGroup.append('g')
	.attr('class','schedContent');

var menuContainer = sketch.append("g")
	.attr("class","woMenu");

var otherContainer = sketch.append("g")
	.attr("class","otherMenu");

var lastMenuWOTop;
if (!vizOnly) {
	woInfo.forEach(function(n,i) {
		n.x = menuLeft;
		n.y = menuWOTop + i * menuWOHgt;
		lastMenuWOTop = n.y
	});
}
// Workout group

var wogroup = menuContainer.selectAll('g')
	.data(woInfo)
	.enter().append("g")
	.attr("class","woItem")
	.attr("transform", "translate(" + margin.left + "," + margin.top + ")")
	.call(d3.drag()
		  .on("start", dragstarted)
		  .on("drag", dragged)
		  .on("end", dragended))
	.on('click', selectMove);

wogroup.append("rect")
	.attr("x", function(d) { return d.x; })
	.attr("y", function(d) { return d.y; })
	.attr("height", menuWOHgt)
	.attr("width", menuWidth)
	.attr("rx",rectRndX)
	.attr("ry",woRectRndY)
	// 2do: non-redundant rgb?
	.style("fill", function(d) {return fillColor(d.measure)})
	.style("stroke", function(d) {return strokeColor(d.measure)})

	.style("fill-opacity", function(d) {
		var opacity;
		if (d.parent==d.name) { opacity = 1.0 }
		else { opacity = 0.6; };
		return opacity;});

var transStr = `translate( ${Math.round(menuWidth * 0.5)}, ${Math.round(menuWOHgt * 0.5)} )` ;

wogroup.append("text")
	.text(function(d) { 
		var lbl;
		if (d.access == '') {
			lbl = d.name; 
		} else {
			lbl = `${d.name} (${d.access})`;
		}
		return lbl; 
	} )
	.attr("class","moveName")
	.attr("x", function(d) { return d.x; })
// NB: nudge WO labels down a bit
	.attr("y", function(d) { return d.y + 3; })
	.attr("transform", transStr)
    .style('fill', 'black')
    .style('font-size', woFontSize)
    .style('text-anchor', 'middle') ;


if (!vizOnly) {
	// NB: Add coolDown as another child of menuContainer

	var coolDown = 	menuContainer.append('g')
		.attr("class","coolDown")
		.attr("transform", `translate( ${margin.left}, ${margin.top} )`)
		.call(d3.drag()
			  .on("start", dragstarted)
			  .on("drag", dragged)
			  .on("end", dragended))
		.on('click', selectMove)
		.datum(cdData);

	var cdRect = coolDown.append("rect")
		.attr("x", menuLeft)
		.attr("y", lastMenuWOTop +  menuWOHgt)
		.attr("height", menuWOHgt)
		.attr("width", menuWidth)
		.style("fill","white")
		.style("stroke","black");

	var cdText = coolDown.append("text")
		.attr("x", menuLeft + Math.round(menuWidth * 0.5))
		.attr("y", lastMenuWOTop +  menuWOHgt + Math.round(menuWOHgt * 0.5) + 3)
		.text("Cool down")
		.style('font-size', woFontSize)
		.style('text-anchor', 'middle');
}

// Other exercises

if (!vizOnly) {
	otherInfo.forEach(function(n,i) {
		n.x = menuOtherLeft;
		n.y = menuOtherTop + (i) * menuOtherHgt;
	});
}

var otherGroup = otherContainer.selectAll('g')
	.data(otherInfo)
	.enter().append("g")
	.attr("class","ogItem")
	.attr("transform", `translate( ${margin.left}, ${margin.top} )`)
	.call(d3.drag()
		  .on("start", dragstarted)
		  .on("drag", dragged)
		  .on("end", dragended))
	.on('click', selectMove);

otherGroup.append("rect")
	.attr("x", function(d) { return d.x; })
	.attr("y", function(d) { return d.y; })
	.attr("height", menuOtherHgt)
	.attr("width", menuWidth)
	.attr("rx",rectRndX)
	.attr("ry",woRectRndY)
	// 2do: non-redundant rgb?
	.style("fill", function(d) {return fillColor(d.measure)})
	.style("stroke", function(d) {return strokeColor(d.measure)})

	.style("fill-opacity", function(d) {
		var opacity;
		if (d.parent==d.name) { opacity = 1.0 }
		else { opacity = 0.6; };
		return opacity;});

var otransStr = `translate( ${Math.round(menuWidth * 0.5)}, ${Math.round(menuOtherHgt * 0.5)} )` ;

otherGroup.append("text")
	.text(function(d) { return `${d.name} (${d.access})` ; } )

	.attr("x", function(d) { return d.x; })
	// NB: nudge text down
	.attr("y", function(d) { return d.y + 2; })
	.attr("transform", otransStr)		     
    .style('fill', 'black')
    .style('font-size', otherFontSize)
    .style('text-anchor', 'middle') ;


function dragstarted(d) {
	
	if (this.hasAttribute("dropped")) { 
	  	// console.log('dragStart-prevDrop '+d.name)
	  	return; }
	
	d3.select(this).raise().classed("active", true);
}

function dragged(d) {
	if (this.hasAttribute("dropped")) { 
	  	// console.log('drag-prevDrop '+d.name)
	  	return; }

	d3.select(this).select("text")
	    .attr("x", d.x = d3.event.x)
	    .attr("y", d.y = d3.event.y);
	d3.select(this).select("rect")
	    .attr("x", d.x = d3.event.x)
	    .attr("y", d.y = d3.event.y);

}

function dragended(d) {
	// register dragged move into hourSched

	if (this.hasAttribute("dropped")) { 
	  	// console.log('dragEnd-prevDrop '+d.name)
	  	return; }

	this.parentElement.removeChild(this);
	d3.select(this).attr('dropped', true);
	d3.select(this).classed("active", false);

	var newSlot = {'schedIdx': 0,
				   'duration': [1,'x'],
				   'slotFiller': d};
	schedList.push(newSlot);

	update();

}

function selectMove(d) {
	// protect click from drag
	if (d3.event.defaultPrevented) return; 

	var circP = d.slotFiller instanceof Array;
	var slotIdx = schedList.findIndex(function(e) {return e.schedIdx == d.schedIdx ; });

	var minuteIncrement = 5;
	
	if (d3.event.shiftKey) {
		// merge this schedSlot into a CIRCUIT with the one above

		var prevSlot = schedList[slotIdx-1];
		if (!(prevSlot.slotFiller instanceof Array)) {
			// NB: push this slot's move duration into its data!
			var prevFiller = prevSlot.slotFiller;
			prevFiller.duration = prevSlot.duration;
			prevSlot.slotFiller = [ prevFiller ];

			// initialize circuit's nrep
			prevSlot.duration = [1,'x'];

		}

		var currFiller = d.slotFiller;
		// NB: push this slot's move duration into its data!
		currFiller.duration = d.duration;
		prevSlot.slotFiller.push(currFiller);

		
		schedList.splice(slotIdx,1);
		
	};
	
	update();
}

function bldNRep(parent,d) {
	// 180512
	// return simplified integer+unit TEXT

	var nrepWid = '80px'; // '65px';
	var nrepHgt = `${schedMoveHgt}px`;
	var nrepFont = `${nrepFontSize}`;

	var ypos;
	if (d.circuit) {
		ypos = Math.round(d.y + ((d.slotFiller.length - 1) * schedMoveHgt/2.));
	} else {
		ypos = d.y };

	var nrepElement;
	
	if (vizOnly) {
		// HACK: why does vizOnly require additional bump down schedMoveHgt/2.
		ypos = Math.round(ypos + schedMoveHgt/2.);
		
		var nrepTxt = d3.select(parent).append("text")
			.attr("x", d.x + circBorderWid)
			.attr("y", ypos)
			.text(function() {return d.duration[0]+d.duration[1];})
			.attr("style", `width: ${nrepWid}; height: ${nrepHgt}; font-size: ${nrepFont}`);
		
		nrepElement = nrepTxt;

	} else {
	        var foid = d.slotFiller.idx+"_bldNRep";
		var frm = d3.select(parent).append("foreignObject")
		        .attr("id",foid)
			.attr("x", d.x + circBorderWid)
			.attr("y", ypos)
	                // Firefox requires foreignObject to have width and height attributes (NOT style attributes!)
	                .attr("width", nrepWid)
	                .attr("height", nrepHgt);
		
		var inpForm = frm
			.attr("x", d.x + circBorderWid)
			.attr("y", ypos)
			.append("xhtml:form");
		
		inpForm.append("input")
			.attr('id','nrepi')

			.attr("value", function() {
				// nasty spot to place this call, but here we are sure that the <input> tag is available
				// and is handily pointed at by 'this':
				this.focus();
				
				return d.duration[0]+d.duration[1];
			})
	    // NB: width needs to > all text, or it disappears!?
		
			.attr("style", `width: ${nrepWid}; height: ${nrepHgt}; font-size: ${nrepFont}`)
        
        // make the form go away when hit ENTER:
			.on("keypress", function(d) {
				// console.log("keypress", this, arguments);
				
				var ev = d3.event;
				// RETURN (Tab=11 doesn't work?!) causes post
	            if (ev.keyCode == 13) {

					if (typeof(ev.cancelBubble) !== 'undefined') // IE
						ev.cancelBubble = true;
					if (ev.stopPropagation)
						ev.stopPropagation();
					ev.preventDefault();

					var txt = inpForm.nodes()[0][0].value;
					// ASSUME: reps units (x,s,f,...) are SINGLE CHAR!
					d.duration[0] = Number(txt.substring(0,txt.length-1));
					d.duration[1] = txt.substring(txt.length-1);

					// odd. Should work in Safari, but the debugger crashes on this instead.
					// Anyway, it SHOULD be here and it doesn't hurt otherwise.
					
       				// console.log('bldNRep: '+d.slotFiller.idx +' '+ d.duration[0]+d.duration[1]);
					update();
				}
			});
		nrepElement = inpForm;
	}
	
	return nrepElement;
}


function editAnnote(textDOM,d) {
	var parent = d3.select(textDOM);

	var annoteWid = circuitWid - 20;
	var annoteHgt = schedMoveHgt - 20;

	var foid = d.slotFiller.idx+"_editAnnote";
	var frm = parent.append("foreignObject")
	          .attr("id", foid)
                  // Firefox requires foreignObject to have width and height attributes (NOT style attributes!)  
	          .attr("width", annoteWid)
	          .attr("height", annoteHgt);

	var idstr = d.slotFiller.idx+"_editNote";
	var inp = frm.attr('id',idstr)
		.attr("x", circuitLeft)
		.attr("y", function(d) { return schedTop + d.schedIdx * schedMoveHgt + 10; })
		.append("xhtml:form")
        .append("input")
        .attr("value", function() {
            // nasty spot to place this call, but here we are sure that the <input> tag is available
            // and is handily pointed at by 'this':
            this.focus();

            return d.annote;
        })
	    // NB: width needs to > all text, or it disappears!?
		.style('text-anchor', 'end')

        .attr("style", `text-anchor: end; width: ${annoteWid}px; height: ${annoteHgt}px; font-size: ${annoteFontSize}`)
    
    // make the form go away when hit ENTER:

        .on("keypress", function() {
            // console.log("keypress", this, arguments);
            
            var ev = d3.event;
			// RETURN (Tab=11 doesn't work?!) causes post
	        if (ev.keyCode == 13) {
                if (typeof(ev.cancelBubble) !== 'undefined') // IE
                    ev.cancelBubble = true;
                if (ev.stopPropagation)
                    ev.stopPropagation();
                ev.preventDefault();

                var txt = inp.node().value;

				d.slotFiller.annote = txt;

				// Note to self: frm.remove() will remove the entire <g> group! Remember the D3 selection logic!
	            this.parentNode.remove();
                
      			// console.log('editName: '+d.slotFiller.idx +' '+ d.slotFiller.annote);
                update();
                
            }
        });
}

function update() {

	// update all slots' schedIdx
	var schedIdx = 0;
	for (var i=0; i< schedList.length; i++) {
		var schedSlot = schedList[i];
		schedSlot.schedIdx = schedIdx++;
		if (schedSlot.slotFiller instanceof Array) {
			schedSlot.circuit = true;
			for (var j=0; j< schedSlot.slotFiller.length; j++) {
				var child = schedSlot.slotFiller[j];
				child.schedIdx = schedIdx++;
			}
		} else {
			schedSlot.circuit = false;
		}
	}

	var parent = d3.select('.schedContent');
	// data() selects existing AND entering elements
	var schedListData = parent.selectAll('.schedSlot')
		.data(schedList,function(d) {return [d]; }); // NB: use entire data object as key

	var newSlots = schedListData.enter()
		.append("g")
		.attr("class","schedSlot");

	var schedListDOM = newSlots.merge(schedListData); 

	// add rect for simple single movements
	newSlots.filter(function(d,i,j) {return ! d.circuit;	})
		.append("rect")
		.attr('class','moveRect1')
		.attr("x", function(d) { d.x = schedLeft; return d.x;} )
		.attr("y", function(d) { d.y = schedTop + d.schedIdx * schedMoveHgt; return d.y; } )
		.attr("height", schedMoveHgt)
		.attr("width", schedWid)
		.style("fill", function(d) { return fillColor(d.slotFiller.measure); })
		.style("stroke", function(d) { return strokeColor(d.slotFiller.measure); })
		.on('click',selectMove); // make rectangle the click target

	// ... also text for simple single movements
	newSlots.filter(function(d,i) {{return ! d.circuit;	}})
		.append("text")
		.text(function(d) {
			var lbl;
			if (d.slotFiller.access == '') {
				lbl = d.slotFiller.name; 
			} else {
				lbl = `${d.slotFiller.name} (${d.slotFiller.access})`;
			}
			return lbl; 
		})
		.attr("x", function(d) { return (d.slotFiller.idx==0 ? circuitLeft+10 : (schedLeft + Math.round(schedWid * 0.5))); })
		.attr("y", function(d) { return schedTop + d.schedIdx * schedMoveHgt + Math.round(schedMoveHgt * 0.5); })
	     // NB: make warmup, cooldown flush left
		.style('text-anchor', function(d) { return (d.slotFiller.idx==0 ? 'start' : 'middle'); })
		.style('font-size', schedFontSize);

	// add annotation to warmup, cool-down

	newSlots.filter(function(d,i) {return d.slotFiller.idx==0; })
		.each(function(d,i) {
			var slot = d3.select(this);
			
			var annote = 
				// 2do: make annotation a textAREA
				// slot.append("textarea")
				// .attr("columns", 60)
				// .attr("rows", 10)
				
				// start with UNFILLED text
				slot.append("text") 
				.text(function(d) {return d.slotFiller.annote;})
				.attr('class','annote')
			    
			     // NB: make warmup, cooldown annote flush right
				.style('text-anchor', 'end')
				.attr("x",schedRight)
				.attr("y", function(d) { return schedTop + d.schedIdx * schedMoveHgt + 10; })
				.attr("width", circuitWid-20)
				.attr("height", schedMoveHgt-20 )
				.style('font-size', annoteFontSize)
			
				.on('click', function () {
					editAnnote(this.parentNode,d);
					// console.log('edit annotation');
				})
				
				// 2do: why doesn't WRAP work?!
				// .call(wrap0,circuitWid-20);
			
			// wrap(annote,circuitWid-20);

		}); // eo-annote-each

	var someCircuits = schedList.some(function (d) {return d.circuit } );

	if (someCircuits) {
		// NB: need to use someCircuits check if something exists for filter() ?!
		var circuits = schedListDOM
			.filter(function(d) {return  d.circuit; });


		var newCircuits = schedListData.enter()
			.filter(function(d) {return  d.circuit; })
			.append('g')
			.attr('class','schedSlot circuit') ;
		    // NB:  need a FUNCTION to capture groups
		    // https://stackoverflow.com/a/24962966/1079688
		    // The data function will be called once for each element in
		    // parentSelection, and it must return an array of data to be used as for
		    // children of that parent element.
			// .data(function(d) {return d.slotFiller;} );
		
			
		var allCircuits = newCircuits.merge(circuits);

		// add LOWER rect0 REPEAT; attach nrep click to it
		allCircuits.append("rect")
			.attr('class','circRect0')
			.attr("x", function(d) { return schedLeft; } )
			.attr("y", function(d) { return schedTop + d.schedIdx * schedMoveHgt; } )
			.attr("height", function(d,i) { return Math.round(schedTop + d.slotFiller.length * schedMoveHgt + circBorderWid); })
			.attr("width", function(d) { return schedWid; })
			.style("fill", "white" )
			.style("stroke", "black") 
			.style("stroke-width", circBorderWid)
			// give this outer rect clicks in the margin for circuit's nrep
			.on('click',selectMove);

		allCircuits.append("rect")
			.attr('class','circRect1')
			.attr("x", circuitLeft)
			.attr("y", function(d) { return schedTop + Math.round(d.schedIdx * schedMoveHgt); } )
			.attr("height", function(d,i) { return schedTop + d.slotFiller.length * schedMoveHgt; })
			.attr("width", circuitWid)
			.style("fill", "white" )
			.style("stroke", 'black')
			.style("stroke-width", 2*circBorderWid);

		allCircuits.each(function(d,i) {
			var nrepForm = bldNRep(this,d);
			this.append(nrepForm);
		});


		// each(): Invokes the specified function for each selected element, in order,
		// being passed the current datum (d), the current index (i), and the
		// current group (nodes), with this as the current DOM element
		// (nodes[i]).
		// cf. nested selections using each() https://bl.ocks.org/mbostock/4c5fad723c87d2fd8273
		allCircuits.each(function(d,i) {
			for(var si=0; si<d.slotFiller.length; si++) {
				updateCircSlot(si,d.slotFiller[si],this);
			}
		});
						 
	} // eo-circuit

	// Nreps for all
	// NB: must be last to be seen above rect?!  even with z-index?!

	newSlots.each(function(d,i) {
		var nrepForm = bldNRep(this,d);
		this.append(nrepForm);
	});

    
	// Only nrep,annote text updatable
	schedListData.select('.nrep')
		.text(function(d,i) { return `${d.duration[0]}${d.duration[1]}`; });
	
	schedListData.select('.annote')
		.text(function(d,i) { return d.slotFiller.annote; });
	
	schedListData.exit().remove();


}

function updateCircSlot(si,slotFiller,thisObj) {
		
	// complete circuits' constituent moves

	var circ = d3.select(thisObj);

	// console.log("updateCircSlot: sfType="+typeof(slotFiller)+" slotFiller="+slotFiller+" si="+si+" keys"+Object.keys(slotFiller));

	// NB: need to get first element of circ.data() array ?!
	var circuitSchedIdx = circ.data()[0].schedIdx;
	
	circ.append("rect")
		.attr("x", circuitLeft)
		.attr("y", function() {
			return schedTop + Math.round( (circuitSchedIdx + si) * schedMoveHgt); } )
		.attr("height", schedMoveHgt)
		.attr("width", circuitWid)
		.style("fill", function() { return fillColor(slotFiller.measure); })
		.style("stroke", function() { return strokeColor(slotFiller.measure); })
		.on('click',selectMove);
	
	circ.append("text")
		.text(function() {
			var lbl;
			if (slotFiller.access == '') {
				lbl = slotFiller.name; 
			} else {
				lbl = `${slotFiller.name} (${slotFiller.access})`;
			}
			return lbl; 
		})
		.attr("x", function() { return schedLeft + schedWid; } ) // NB: flush-right
		.attr("y", function() { return schedTop + Math.round( (circuitSchedIdx + si + 0.5) * schedMoveHgt); })
		.style('text-anchor', 'end')
		.style('font-size', schedFontSize);
	
	circ.append("text")
		.attr('class','nrep')
		.text(function(d2) { return `${slotFiller.duration[0]}${slotFiller.duration[1]}`; })
		.attr("x", circuitLeft )
		.attr("y", function() {
			// NB: don't need to check for this being a circuit!
			var movePos =  Math.round(schedMoveHgt * (circuitSchedIdx + si + 0.5));
			return schedTop + movePos;
		})
		.style('font-size', nrepFontSize)
		.style('text-anchor', 'start') ;
	
}

function collectSched() {
	var input = document.createElement("input");
	input.type = "hidden";
	input.name = "schedList";
	input.value = JSON.stringify(schedList);
	$('#wosForm').append(input);  

	input = document.createElement("input");
	input.type = "hidden";
	input.name = "mesoIdx";
	input.value = mesoIdx;
	$('#wosForm').append(input);  

	input = document.createElement("input");
	input.type = "hidden";
	input.name = "week";
	input.value = week;
	$('#wosForm').append(input);  

	input = document.createElement("input");
	input.type = "hidden";
	input.name = "dayIdx";
	input.value = dayIdx;
	$('#wosForm').append(input);  

	input = document.createElement("input");
	input.type = "hidden";
	input.name = "schedIdx";
	input.value = schedIdx;
	$('#wosForm').append(input);  
	
}

	// Initialize schedule with warmup

// NB: schedListDOM initialized with warmUpSMove above
if (!vizOnly) {
	schedList = [wuSlot];
};

update();
