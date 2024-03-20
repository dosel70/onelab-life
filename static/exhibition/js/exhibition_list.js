const likes = document.querySelectorAll("button.WishButton_button");

likes.forEach((like) => {
    const color = document.getElementsByClassName("is");
    like.addEventListener("click", (e) => {
        // console.log(e.target.classList);
        e.target.classList.toggle("active");
        e.ariaPressed = "true";
    });
});

const lists = document.querySelectorAll(".css-qn01ot");
const writeList = document.querySelectorAll("div.css-ivvewn");

lists.forEach((list) => {
    list.addEventListener("mouseover", (e) => {
        list.classList.add("list-active");
        // console.log(list.children[1]);
        // list.children[1].style.display = "block";
    });

    list.addEventListener("mouseout", (e) => {
        list.classList.remove("list-active");
        // list.children[1].style.display = "none";
    });
});
