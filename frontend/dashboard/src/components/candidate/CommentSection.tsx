import {
    useEffect,
    useState
} from "react";


import api from "../../api/axios";


import type {
    CandidateDetailType
} from "../../types/candidate";



interface CommentType {

    id:number;

    author:string;

    role:string;

    comment:string;

    created_at:string;

    updated_at?:string;

}




interface Props {

    candidate: CandidateDetailType;

    onUpdate?:()=>void;

}







function CommentSection({

    candidate,

    onUpdate

}:Props){



    const [
        comments,
        setComments
    ] = useState<CommentType[]>([]);




    const [
        text,
        setText
    ] = useState("");




    const [
        role,
        setRole
    ] = useState("HR");




    const [
        loading,
        setLoading
    ] = useState(false);

    const [
        editingId,
        setEditingId
    ] = useState<number|null>(null);

    const [
        editText,
        setEditText
    ] = useState("");







    async function fetchComments(){


        try{


            const res = await api.get(

                `/candidates/${candidate.candidate_id}/comments`

            );


            setComments(

                res.data.data ?? []

            );


        }

        catch(error){

            console.error(
                error
            );

        }


    }







    useEffect(()=>{


        fetchComments();


    },[
        candidate.candidate_id
    ]);








    async function addComment(){


        if(!text.trim())
            return;



        try{


            setLoading(true);



            await api.post(

                `/candidates/${candidate.candidate_id}/comments`,

                {

                    comment:text,

                    role:role,

                    author:
                        role === "HR"
                        ?
                        "HR Admin"
                        :
                        "Line Manager"

                }

            );



            setText("");



            await fetchComments();



            if(onUpdate){

                onUpdate();

            }


        }


        catch(error){

            console.error(
                error
            );

        }


        finally{


            setLoading(false);


        }


    }

    async function updateComment(id:number){

        await api.put(
            `/candidates/comments/${id}`,
            {
                comment:editText
            }
        );


        setEditingId(null);

        setEditText("");

        fetchComments();

    }

    async function deleteComment(id:number){

        if(
            !confirm(
                "Delete this comment?"
            )
        )
            return;


        await api.delete(
            `/candidates/comments/${id}`
        );


        fetchComments();

    }



    function roleStyle(

        value:string

    ){


        if(value==="Line Manager"){

            return {

                border:
                "border-purple-200",

                badge:
                "bg-purple-50 text-purple-600"

            };

        }



        return {

            border:
            "border-blue-200",

            badge:
            "bg-blue-50 text-blue-600"

        };


    }








    return (


        <section

            className="
            bg-white
            border
            rounded-2xl
            p-5
            "

        >



            {/* HEADER */}


            <div

                className="
                mb-5
                "

            >


                <h2

                    className="
                    text-sm
                    font-bold
                    text-gray-900
                    uppercase
                    "

                >

                    Recruitment Collaboration & Feedback

                </h2>



                <p

                    className="
                    text-xs
                    text-gray-400
                    mt-1
                    "

                >

                    Comments and feedback history

                </p>


            </div>









            {/* COMMENT LIST */}


            <div

                className="
                space-y-5
                mb-6
                "

            >


                {

                comments.length > 0

                ?

                comments.map(comment=>{


                    const style =
                        roleStyle(
                            comment.role
                        );



                    return (

                        <div

                            key={
                                comment.id
                            }

                            className={`
                            border-l-2
                            pl-4
                            ${style.border}
                            `}

                        >



                            <div

                                className="
                                flex
                                justify-between
                                items-start
                                "

                            >



                                <div>


                                    <div

                                        className="
                                        flex
                                        items-center
                                        gap-2
                                        "

                                    >


                                        <p

                                            className="
                                            text-sm
                                            font-semibold
                                            text-gray-800
                                            "

                                        >

                                            {
                                                comment.author
                                            }

                                        </p>



                                        <span

                                            className={`
                                            text-xs
                                            px-2
                                            py-0.5
                                            rounded-full
                                            ${style.badge}
                                            `}

                                        >

                                            {
                                                comment.role
                                            }

                                        </span>


                                    </div>



                                </div>





                                <p

                                    className="
                                    text-xs
                                    text-gray-400
                                    "

                                >

                                    {
                                        new Date(
                                            comment.created_at
                                        )
                                        .toLocaleString(
                                            "en-GB",
                                            {
                                                dateStyle:
                                                    "medium",

                                                timeStyle:
                                                    "short"
                                            }
                                        )
                                    }
                                    {
                                        comment.updated_at
                                        &&
                                        <p

                                            className="
                                            text-xs
                                            text-gray-400
                                            mt-1
                                            "

                                        >

                                            Edited by {comment.author} at{" "}

                                            {
                                                new Date(
                                                    comment.updated_at
                                                )
                                                .toLocaleString(
                                                    "en-GB",
                                                    {
                                                        dateStyle:"medium",
                                                        timeStyle:"short"
                                                    }
                                                )
                                            }


                                        </p>
                                    }


                                </p>


                            </div>






                            {
                                editingId === comment.id

                                ?

                                <div className="mt-2">

                                    <textarea

                                        value={editText}

                                        onChange={
                                            e =>
                                            setEditText(
                                                e.target.value
                                            )
                                        }

                                        className="
                                        w-full
                                        border
                                        rounded-lg
                                        p-2
                                        text-sm
                                        "

                                    />


                                    <div

                                        className="
                                        flex
                                        gap-2
                                        mt-2
                                        "

                                    >

                                        <button

                                            onClick={() =>
                                                updateComment(
                                                    comment.id
                                                )
                                            }

                                            className="
                                            bg-blue-600
                                            text-white
                                            text-xs
                                            px-3
                                            py-1
                                            rounded
                                            "

                                        >

                                            Save

                                        </button>



                                        <button

                                            onClick={() => {

                                                setEditingId(null);

                                                setEditText("");

                                            }}

                                            className="
                                            border
                                            text-xs
                                            px-3
                                            py-1
                                            rounded
                                            "

                                        >

                                            Cancel

                                        </button>


                                    </div>


                                </div>


                                :


                                <div>

                                    <p

                                        className="
                                        mt-2
                                        text-sm
                                        text-gray-600
                                        leading-6
                                        "

                                    >

                                        {comment.comment}

                                    </p>



                                    <div

                                        className="
                                        flex
                                        gap-3
                                        mt-2
                                        "

                                    >

                                        <button

                                            onClick={() => {

                                                setEditingId(
                                                    comment.id
                                                );

                                                setEditText(
                                                    comment.comment
                                                );

                                            }}

                                            className="
                                            text-xs
                                            text-blue-600
                                            "

                                        >

                                            Edit

                                        </button>



                                        <button

                                            onClick={() =>
                                                deleteComment(
                                                    comment.id
                                                )
                                            }

                                            className="
                                            text-xs
                                            text-red-500
                                            "

                                        >

                                            Delete

                                        </button>


                                    </div>


                                </div>

                            }


                        </div>

                    );


                })


                :


                <p

                    className="
                    text-sm
                    text-gray-400
                    "

                >

                    No comments yet

                </p>


                }


            </div>









            {/* ADD COMMENT */}


            <div>


                <div

                    className="
                    flex
                    items-center
                    justify-between
                    mb-3
                    "

                >


                    <label

                        className="
                        text-sm
                        text-gray-600
                        "

                    >

                        Add feedback as

                    </label>




                    <select

                        value={
                            role
                        }


                        onChange={

                            e=>

                            setRole(
                                e.target.value
                            )

                        }


                        className="
                        border
                        rounded-lg
                        px-3
                        py-1.5
                        text-sm
                        "

                    >

                        <option value="HR">

                            HR

                        </option>


                        <option value="Line Manager">

                            Line Manager

                        </option>


                    </select>


                </div>






                <textarea


                    value={
                        text
                    }


                    onChange={

                        e=>

                        setText(
                            e.target.value
                        )

                    }


                    rows={4}


                    maxLength={500}


                    placeholder="Add feedback..."


                    className="
                    w-full
                    border
                    border-gray-200
                    rounded-xl
                    p-3
                    text-sm
                    resize-none
                    focus:outline-none
                    focus:ring-2
                    focus:ring-blue-200
                    "

                />





                <div

                    className="
                    flex
                    justify-between
                    items-center
                    mt-2
                    "

                >


                    <span

                        className="
                        text-xs
                        text-gray-400
                        "

                    >

                        {
                            text.length
                        }

                        /500

                    </span>





                    <button


                        disabled={
                            loading
                        }


                        onClick={
                            addComment
                        }


                        className="
                        px-4
                        py-2
                        rounded-xl
                        bg-blue-600
                        text-white
                        text-sm
                        hover:bg-blue-700
                        disabled:opacity-50
                        "

                    >


                        {

                        loading

                        ?

                        "Adding..."

                        :

                        "Add Comment"

                        }


                    </button>



                </div>



            </div>






        </section>

    );

}




export default CommentSection;