var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
var controls = [];

class controlObject {
	constructor(name) {
		this.name=name;
		this.value=0;
	}

	listen() {
		let self = this;
		socket.on(this.name,function(msg) {
			self['value'] = msg.value;
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
