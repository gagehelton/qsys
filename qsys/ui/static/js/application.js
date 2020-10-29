var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');


$(document).ready(function(){
    //connect to the socket server.
    //var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var numbers_received = [];

    //receive details from server
    socket.on('newvalue', function(msg) {
        console.log("Received number" + msg.number);
        //maintain a list of ten numbers
        if (numbers_received.length >= 10){
            numbers_received.shift()
        }            
        numbers_received.push(msg.number);
        numbers_string = '';
        for (var i = 0; i < numbers_received.length; i++){
            numbers_string = numbers_string + '<p>' + numbers_received[i].toString() + '</p>';
        }
        $('#log').html(numbers_string);
    });

});

/*
function listen() {
	return socket.on('payload',function(msg){
		return msg;
	});
}

*/


class controlObject {
	constructor(name) {
		this.name = name;
		this.value = 0;
	}

	listen() {
		socket.on(this.name,function(msg) {
			console.log('rx' + msg.value)
		});
		
	}
}

$(document).ready(function(){

	//controls = []

	//let payload = listen();
	//console.log(payload);

	/*(for (i=0; i < payload.length; i++) {
		controls.push(new controlObject(payload[i]));
		console.log(controls);
		controls[-1].listen();
	}*/

	let test = new controlObject("namedControlInQsysDesigner")
	test.listen()
});
