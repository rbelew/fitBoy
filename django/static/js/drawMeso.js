var altKey;

var schedType;

var MeasureColor = {"Assault Bike": [255, 153, 51], 
					"Split Squat": [255,0,0],
					"TB Deadlift": [255,255,0],
					"Pull-Up": [164,194,244],
					"Push-Up": [182,215,168],
					"Turkish Get-Up" : [180,167,214],
					"OPEN": [230,230,230],          // 90% white
					"Hip CAR": [255, 102, 204]
				   };

var TestMeasureColor = {"able": [230,230,230],
						"baker": [255,0,0],
						"charlie": [255,255,0],
						"dog": [164,194,244] };

// Globals
var moveData = [];


// Utilities


function keepNumeric(k, v) {
	// https://stackoverflow.com/a/10563962
    return (typeof v === "object" || isNaN(v)) ? v : parseInt(v) ;
}

function rptD3data(indata,lbl) {

	var data = svg.selectAll(".movemt").data();
	for (var i=0; i<data.length; i++) {
		var d = data[i];
		console.log(lbl+' '+i+' '+d.name+' '+d.x+' '+d.y);
	}
}

function round(p, n) {
	return p % n < n / 2 ? p - (p % n) : p + n - (p % n);
}

function bldRGBSpec(name) {
	if (!MeasureColor.hasOwnProperty(name))
		name = "OPEN";
	var rgb = MeasureColor[name]; // TestMeasureColor[name]; // 
	rgbStr = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
	// console.log('bldRGBSpec: ' + name + ': ' + rgbStr);
	return rgbStr;
}
	
function getIdx(s) {
	var bits = s.split('_');
	return bits[1];
}

function getName(s) {
	var bits = s.split('_');
	return bits[2];
}
function getTask(s) {
	var bits = s.split('_');
	return bits[3];
}

function padInt(i,len) {
	return i.toString().padStart(len,'0');
}

function drawSchedGrid(audience) {

	// create grid lines
	svg.selectAll('.vertical')
	    .data(d3.range(1, nsession))
	  .enter().append('line')
	    .attr('class', 'vertical')
	    .attr('x1', function(d) { return d * moveWid; })
	    .attr('y1', 0)
	    .attr('x2', function(d) { return d * moveWid; })
	    .attr('y2', height);
	
	svg.selectAll('.horizontal')
	    .data(d3.range(1, 2*nweek))
	  .enter().append('line')
	    .attr('class', 'horizontal')
	    .attr('x1', 0)
	    .attr('y1', function(d) { return d * moveHgt; })
	    .attr('x2', width)
	    .attr('y2', function(d) { return d * moveHgt; })
		.style('stroke-width', function(d,i) { return ((i % 2) ? 10 : 1) });
}

function collectMoveSeq() {
	// capture position-> schedule for all moves
	// return moveSched: week -> session -> [move1,move2]
	// ASSUME two moves/workout

	var moveSched = {};
	var maxWeek=0;
	var maxSession=0;

	var moveDOM = 	svg.selectAll(".movemt").data()

	// sort moves, DESCENDING by row/week, then col/session
	moveDOM.sort(function cmp(a,b) {
		var ak = padInt(a.y,3) + '_' + padInt(a.x,3);
		var bk = padInt(b.y,3) + '_' + padInt(b.x,3);
		return ak > bk; 
	});

	for (var i=0; i<moveDOM.length; i++) {
		// moveDOM.forEach(function(move) {
		var move = moveDOM[i];
		// NB: need to increment x,y slightly
		var sessionIdx = Math.floor((move.x + 1) / moveWid);
		var weekIdx = Math.floor((move.y + 1) / (2 * moveHgt)); // ASSUME two moves/session
		var woParity = Math.floor((move.y + 1) / moveHgt) % 2;
		
		if (!(weekIdx in moveSched)) {
			moveSched[weekIdx] = {};
		}

		if (!(sessionIdx in moveSched[weekIdx])) {
			moveSched[weekIdx][sessionIdx] = ['OPEN','OPEN'];
		}

		moveSched[weekIdx][sessionIdx][woParity] = move;
		
		if (weekIdx > maxWeek) {
			maxWeek = weekIdx;
		}

		if (sessionIdx > maxSession) {
			maxSession = sessionIdx;
		}
		// console.log(i+' '+move.name);
		
	};

	var moveSchedStr = JSON.stringify(moveSched);
	console.log('collectMoveSeq '+maxWeek+' '+moveSchedStr);

	// NB: need to use sessionStorage to maintain moveSched for collectMeso()
	sessionStorage.setItem('moveSched',moveSchedStr);
	
	return [maxWeek,maxSession,moveSched];
}

function collectMeso() {
	// collect moveSched, includeQual, schedQual, excludeAccry
	
	// NB: need to use sessionStorage to maintain moveSched from collectMoveSeq(), repeatToFill()
	var moveSched = sessionStorage.getItem('moveSched');

	var input = document.createElement("input");
	input.type = "hidden";
	input.name = "moveSeq";
	input.value = moveSched;
	$('#mesoForm').append(input);

	var includeQualStr = JSON.stringify(includeQual);
	var input = document.createElement("input");
	input.type = "hidden";
	input.name = "includeQual";
	input.value = includeQualStr;
	$('#mesoForm').append(input);

	// schedQualTbl: idx -> value
	var schedQualTbl = {};
	d3.selectAll('.rating')
		.each(function (d,i) {

			console.log(this.id + ' ' + this.value);
			schedQualTbl[this.id] = this.value;
		});
	var schedQualTblStr = JSON.stringify(schedQualTbl);
	var input = document.createElement("input");
	input.type = "hidden";
	input.name = "schedQual";
	input.value = schedQualTblStr;
	$('#mesoForm').append(input);

	// get non-checked as excludeAccry
	var excludeAccry=[];
	d3.select('#accessList')
		.selectAll('input')
		.each(function(d,i) {
			if (! this.checked) {
				excludeAccry.push(this.id);
			}
		});
	var excludeAccryStr = JSON.stringify(excludeAccry);
	var input = document.createElement("input");
	input.type = "hidden";
	input.name = "excludeAccry";
	input.value = excludeAccryStr;
	$('#mesoForm').append(input);

}
	
function repeatToFillCohort() {
	// use currently specified weeks' moves as schema to fill out rest of schedule

	var [maxWeek,maxSession,moveSched] = collectMoveSeq();

	
	if (maxWeek >= nweek) {
		return moveSched;
	}

	var nweek2repeat = maxWeek+1;
	// NB: count current template as FIRST repeat
	// NB: ceil() because we need to ensure filling all nsession
	var nrepeat = Math.ceil(nweek / nweek2repeat) - 1;
	var templateJSON={};
	for (var iw=0; iw <= maxWeek; iw++) {
		// NB: deep clone required, can't use shallow Object.assign()
		// https://stackoverflow.com/a/5344074

		// NB: using hack to maintain number indices!
		
		// NB: don't bother to re-parse for template here; done   below!
		// template[iw] = JSON.parse(JSON.stringify(template[iw]));

		templateJSON[iw] = JSON.stringify(moveSched[iw],keepNumeric);
	}
	
	for (var irepeat=1; irepeat<= nrepeat; irepeat++) {
		for (var iw=0; iw < nweek2repeat; iw++) {
			var weekIdx = irepeat * nweek2repeat + iw;
			if (weekIdx > nweek-1)
				break;
			moveSched[weekIdx] = JSON.parse(templateJSON[iw]);
		}
	}

	// fill in rest of svg with "ditto" gray
	// NB: two moves/week row
	var schemaHgt = nweek2repeat * 2 * moveHgt;
	
	// NB: d3.range(): start default=0; exclusive stop value
	var repeatSchema = svg.selectAll('.repeatSchema')
	    .data(d3.range(1, nrepeat+1))
		.enter().append('g')
		.attr('x', 0)
		.attr('y', function(d) {return d * schemaHgt; });

	repeatSchema.append('rect')
		.attr('x', 0)
		.attr('y', function(d) { return d * schemaHgt; })
		.attr("width", nsession * moveWid)
		.attr("height", schemaHgt)
		.attr("rx", 20)
		.attr("ry", 20)
		.style("fill", 'rgb(224, 235, 235)')
		.style("fill-opacity", '0.25')
		.style("stroke","black")
		.style("stroke-width",2);

	repeatSchema.append('text')
		.attr('x', nsession * moveWid / 2)
		.attr('y', function(d) { return (d * schemaHgt) + schemaHgt / 2; })
	    .attr("dy", ".35em") // dy=0.35em can help vertically centre text regardless of font size.
		.attr("text-anchor", "middle")
		.attr("font-size", "large")
		.attr("font-style", "italic")
		.text(function(d) { return `Ditto! (${d})` });

	var moveSchedStr = JSON.stringify(moveSched);	
	console.log('repeatToFillCohort: '+moveSchedStr);

	// NB: need to use sessionStorage to maintain moveSched for collectMeso()
	// The keys and the values are always strings
	sessionStorage.setItem('moveSched',moveSchedStr);

	redrawMoveSched();
	
	return moveSched;
}

function repeatToFillIndiv() {
	// use currently specified weeks' moves as schema to fill out rest of schedule

	var [maxWeek,maxSession,moveSched] = collectMoveSeq();

		if (maxSession >= nsession) {
		return moveSched;
	}

	var nsession2repeat = maxSession+1;
	// NB: count current template as FIRST repeat
	// NB: ceil() because we need to ensure filling all nsession
	var nrepeat = Math.ceil(nsession / nsession2repeat) - 1;
	var templateJSON={};
	for (var si=0; si <= maxSession; si++) {
		// NB: deep clone required, can't use shallow Object.assign()
		// https://stackoverflow.com/a/5344074

		// NB: using keepNumeric hack to maintain number indices!
		
		// NB: don't bother to re-parse for template here; done   below!
		// template[iw] = JSON.parse(JSON.stringify(template[iw]));

		// NB: for indiv ASSUME  first/only week
		templateJSON[si] = JSON.stringify(moveSched[0][si],keepNumeric);
	}
	
	for (var irepeat=1; irepeat<= nrepeat; irepeat++) {
		for (var si=0; si < nsession2repeat; si++) {
			// NB: for indiv ASSUME  first/only week
			var sessIdx = irepeat * nsession2repeat + si;
			if (sessIdx > nsession-1)
				break;
			moveSched[0][sessIdx] = JSON.parse(templateJSON[si]);
		}
	}

	// fill in rest of svg with "ditto" gray
	var schemaWid = nsession2repeat  * moveWid;
	
	// NB: d3.range(): start default=0; exclusive stop value
	var repeatSchema = svg.selectAll('.repeatSchema')
	    .data(d3.range(1, nrepeat+1))
		.enter().append('g')
		.attr('x', function(d) {return d * schemaWid; })
		.attr('y', 0);

	repeatSchema.append('rect')
		.attr('x', function(d) {return d * schemaWid; })
		.attr('y', 0)
		.attr("width", schemaWid)
		.attr("height", 2 * moveHgt)
		.attr("rx", 20)
		.attr("ry", 20)
		.style("fill", 'rgb(224, 235, 235)')
		.style("fill-opacity", '0.25')
		.style("stroke","black")
		.style("stroke-width",2);

	repeatSchema.append('text')
		.attr('x', function(d) { return (d * schemaWid) + schemaWid / 2; })
		.attr('y', moveHgt)
	    .attr("dy", ".35em") // dy=0.35em can help vertically centre text regardless of font size.
		.attr("text-anchor", "middle")
		.attr("font-size", "large")
		.attr("font-style", "italic")
		.text(function(d) { return `Ditto! (${d})` });

	var moveSchedStr = JSON.stringify(moveSched);	
	console.log('repeatToFillIndiv: '+moveSchedStr);

	// NB: need to use sessionStorage to maintain moveSched for collectMeso()
	// The keys and the values are always strings
	sessionStorage.setItem('moveSched',moveSchedStr);

	redrawMoveSched();
	
	return moveSched;
}

function redrawMoveSched() {
	// redraw move schedule using sessionStorage.getItem('moveSched')
	// moves no longer draggable

	var moveSchedStr = sessionStorage.getItem('moveSched');
	var moveSched = JSON.parse(moveSchedStr);

	var moveList=[];
	for (weekIdx in moveSched) {
		var sessionList = moveSched[weekIdx];
		for (sessionIdx in sessionList) {
			var sessMoves = moveSched[weekIdx][sessionIdx];
			var smidx = 0;
			sessMoves.forEach(function(dragMove) {
				var move;
				if (dragMove==="OPEN") {
					move = {name: "OPEN",
							task: "OPEN"}
				} else {
					move = Object.assign({},dragMove);
				}
				move.widx = parseInt(weekIdx);
				move.sidx = parseInt(sessionIdx);
				move.smidx = smidx;
				moveList.push(move);
				smidx += 1;
			});  // eo-sessMove
								
		} // eo-session
	} // eo-week

	var moveDOM = svg.selectAll(".movemt")
		.data(moveList, function(d) {return d.name+'_'+d.widx+'_'+d.sidx+'_'+d.smidx; });

	// UPDATE
	moveDOM.attr("class", "movemt");

	// ENTER
	// Create new elements as needed.
	//
	// ENTER + UPDATE
	// After merging the entered elements with the update selection,
	// apply operations to both.
	var moveEnter = moveDOM.enter()
		.append("g", "svg")
		.attr("class", "movemt")
		.attr("name", function(d, i) {return d.name;})
	    .attr("x", function(d, i) {
			var x =  d.sidx * moveWid;
			d.x = x;
			return x; 
		})
			
		.attr("y", function(d, i) {
			var y = (2 * d.widx + d.smidx)  * moveHgt;
			d.y = y;
			return y;
		});
	// NB: no longer draggable
	
 	moveEnter.append("rect")
	    .attr("x", function(d, i) {
			var x = d.sidx * moveWid;
			return x;
		})
		.attr("y", function(d, i) {
			var y = (2 * d.widx + d.smidx)  * moveHgt;
			return y;
		})
		.attr("width", moveWid)
		.attr("height", moveHgt)
		.style("fill", function(d) {return bldRGBSpec(d.name); });

	moveEnter.append("text")
	    .attr("x", function(d, i) {
			var x = d.sidx * moveWid + moveWid/2;
			return x;
		})
		.attr("y", function(d, i) {
			var y = (2 * d.widx + d.smidx) * moveHgt + moveHgt / 2;
			return y;
		})
	
      .attr("dy", ".35em") // dy=0.35em can help vertically centre text regardless of font size.
      .attr("text-anchor", "middle")
      .text(function(d) { return d.task; });

	// redraw grid ON TOP of moves
	drawSchedGrid();
}

function dragstarted(d) {
  d3.select(this).raise().classed("active", true);
}

function dragged(d) {
  var x = d3.event.x,
      y = d3.event.y,
	  gridX = round(Math.max(x, Math.min(moveWid * (x % moveWid), x)), Xresolution),
      gridY = round(Math.max(y, Math.min(moveHgt * (y % moveHgt), y)), Yresolution);
	

	d3.select(this)
		.attr("x", gridX)
		.attr("y", gridY);
	d3.select(this).select("rect")
		.attr("x", gridX)
		.attr("y", gridY);

	d3.select(this).select("text")
		.attr("x", gridX + moveWid / 2)
		.attr("y", gridY + moveHgt / 2);
	
	// console.log('dragged: '+d.name+' x='+d.x+' y='+d.y);
}

function dragended(d) {

  var x = d3.event.x,
      y = d3.event.y,
	  gridX = round(Math.max(x, Math.min(moveWid * (x % moveWid), x)), Xresolution),
      gridY = round(Math.max(y, Math.min(moveHgt * (y % moveHgt), y)), Yresolution);

	d.x = gridX;
	d.y = gridY;
	
	console.log('draggend: '+d.name+' x='+d.x+' y='+d.y);

  d3.select(this).classed("active", false);
}

function change() {
  // clearTimeout(timeout);

  d3.transition()
      .duration(altKey ? 7500 : 750)
      .each(redraw);
}
	
function redraw(evt) {

	// Updated create*Meso.html
	// var moveNames1 = sortSelect.toArray();

	var moveNames = schedQual;
	
	// console.log('redraw: sortSelect:'+moveNames);

	var nidx;
	var fakeJumped = false;

	moveData = [];
	for (nidx in moveNames) {
		var qualName = moveNames[nidx];
		if (qualName==='fakeMeasure') {
			fakeJumped = true;
			continue;
		}
		var idx = getIdx(qualName);
		var nameOnly = getName(qualName);
		var task = getTask(qualName);

		var sortOrder = (fakeJumped ? nidx-1 : nidx);
		var mobj = {idx: idx,
					name: nameOnly,
					task: task,
				    sortOrder: sortOrder};
		
		moveData.push(mobj);
		// console.log('redraw: moveData '+ nidx+' ' + mobj.name);
	}

	// DATA JOIN
	// Join new data with old elements, if any.

	var moveDOM = svg.selectAll(".movemt")
	    // NB: moveNames is multiset; use both sortOrder and name for key, to notice multiples and permutations of sortSelect
		.data(moveData, function(d) {return d.name+'_'+d.sortOrder; });

	// UPDATE
	moveDOM.attr("class", "movemt");

	// ENTER
	// Create new elements as needed.
	//
	// ENTER + UPDATE
	// After merging the entered elements with the update selection,
	// apply operations to both.
	var moveEnter = moveDOM.enter()
		.append("g", "svg")
		.attr("class", "movemt")
		.attr("name", function(d, i) {return d.name;})
		.attr("idx", function(d, i) {return d.idx;})
	    .attr("x", function(d) {
			var x;
			if (schedType==='cohort') {
				x=0;
			} else {
				x = Math.floor(d.sortOrder / 2) * moveWid;
			}
			d.x = x;
			return x; 
		})
			
		.attr("y", function(d) {
			var y;
			if (schedType==='cohort') {
				y = d.sortOrder * moveHgt;
			} else {
				y = d.sortOrder % 2 * moveHgt; 
			}
			d.y = y;
			return y;
		})
	
		.call(d3.drag()
			  .on("start", dragstarted)
			  .on("drag", dragged)
			  .on("end", dragended));

 	moveEnter.append("rect")
	    .attr("x", function(d) {
			var x;
			if (schedType==='cohort') {
				x=0;
			} else {
				x = Math.floor(d.sortOrder / 2) * moveWid;
			}
			return x;
		})
		.attr("y", function(d) {
			var y;
			if (schedType==='cohort') {
				y = d.sortOrder * moveHgt;
			} else {
				y = d.sortOrder % 2 * moveHgt; 
			}
			return y;
		})
		.attr("width", moveWid)
		.attr("height", moveHgt)
		.style("fill", function(d) {return bldRGBSpec(d.name); });

	moveEnter.append("text")
	    .attr("x", function(d) {
			if (schedType==='cohort') {
				return moveWid/2;
			} else {
				return Math.floor(d.sortOrder/2) * moveWid + moveWid/2; 
			}
		})
		.attr("y", function(d) {
			if (schedType==='cohort') {
				return d.sortOrder * moveHgt + moveHgt / 2;
			} else {
				return (d.sortOrder % 2) * moveHgt + moveHgt / 2; 
			}
		})
	
      .attr("dy", ".35em") // dy=0.35em can help vertically centre text regardless of font size.
      .attr("text-anchor", "middle")
      .text(function(d) { return d.task; });

	var moveMerge = moveEnter.merge(moveDOM)
	    .attr("x", function(d) {
			var x;
			if (schedType==='cohort') {
				x=0;
			} else {
				x = Math.floor(d.sortOrder / 2) * moveWid;
			}
			d.x = x;
			return x;
		})
			
		.attr("y", function(d) {
			var y;
			if (schedType==='cohort') {
				y = d.sortOrder * moveHgt;
			} else {
				y = d.sortOrder % 2 * moveHgt;
			}
			d.y = y;
			return y;
		});

	// EXIT
	// Remove old elements as needed.
	moveDOM.exit().remove();

	var moveDOM2 = 	svg.selectAll(".movemt").data()
	var moveDOM2Str = JSON.stringify(moveDOM2);	
	console.log('redraw moveDOM on exit: '+moveDOM2Str);
	
	
}
