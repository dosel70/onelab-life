let page = 1
const getList = (callback) => {
    fetch(`http://3.38.246.56/${page}`)
    .then((response) => response.json())
    .then(() => {
        if(callback){
            callback(exhibitions)
        }
    })
}

getList()