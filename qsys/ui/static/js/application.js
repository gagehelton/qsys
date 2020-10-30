var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
var controls = [];

class volDiv {
	constructor(name) {
		this.name=name;
		this.element = document.createElement('div');
		this.element.id = this.name;
		this.element.className = "progress";
		this.sub_element = document.createElement('div');
		this.sub_element.id = this.name+'_progressbar';
		this.sub_element.setAttribute('class', 'progress-bar progress-bar-striped progress-bar-animated');
		this.sub_element.setAttribute('role','progressbar');
		this.sub_element.setAttribute('aria-valuenow',this.value);
		this.sub_element.setAttribute('aria-valuemin','-100');
		this.sub_element.setAttribute('aria-valuemax','20');
		this.sub_element.setAttribute('style','width: 75%');
		this.element.appendChild(this.sub_element);
		//this.node = document.body.appendChild(this.element);
		//document.body.appendChild(document.createElement('br'));
	}
}

class controlObject {
	constructor(name) {
		this.name=name;
		this.value=0;
		this.ui_element = new volDiv(this.name);
		document.body.appendChild(this.ui_element.element);
		document.body.appendChild(document.createElement('br'));
		
	}

	listen() {
		let self = this;
		socket.on(this.name,function(msg) {
			self['value'] = msg.value;
			document.getElementById(self.name+"_progressbar").setAttribute('style','width: '+self.value+'%');
			console.log(self.name+'-'+self.value);
		});
	}
}

$(document).ready(function(){
	socket.on('payload',function(msg){
		for (i=0; i < msg.length; i++) {
			let tmp = new controlObject(msg[i]);
			//create ui object here!
			controls.push(tmp);
			controls[i].listen();
		}});
});
