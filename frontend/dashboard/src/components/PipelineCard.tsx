interface Props {

    name:string;

    count:number;

    children?:React.ReactNode;

}


function PipelineCard({
    name,
    count,
    children
}:Props){


return (

<div
className="
bg-white
border
rounded-xl
p-5
min-h-[700px]
"
>


<div
className="
flex
justify-between
items-center
mb-5
"
>

<h2
className="
text-xl
font-bold
"
>
{name}
</h2>


<span
className="
bg-gray-200
px-3
rounded-full
"
>
{count}
</span>


</div>


<div>

{children}

</div>


</div>

)

}


export default PipelineCard;